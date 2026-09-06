"""Upload a distribution to PyPI using stdlib only (PEP 517 sdist -> legacy multipart upload).

Mirrors twine's wire protocol: POST multipart/form-data to upload.pypi.org/legacy/
with :action=file_upload, metadata fields from the sdist's PKG-INFO, and digests.
No external dependencies (pip/twine unavailable on this box).
"""
import email
import hashlib
import io
import json
import mimetypes
import os
import sys
import tarfile
import urllib.error
import urllib.request
import uuid


def pkg_info_fields(sdist_path):
    with tarfile.open(sdist_path, "r:gz") as tf:
        for member in tf.getmembers():
            if member.name.endswith("/PKG-INFO"):
                fh = tf.extractfile(member)
                if fh is None:
                    continue
                raw = fh.read().decode("utf-8")
                break
        else:
            raise SystemExit("PKG-INFO not found in " + sdist_path)
    msg = email.message_from_string(raw)
    return raw, msg


def digests(data):
    return {
        "md5_digest": hashlib.md5(data).hexdigest(),
        "sha256_digest": hashlib.sha256(data).hexdigest(),
        "blake2_256_digest": hashlib.blake2b(data, digest_size=32).hexdigest(),
    }


def build_body(fields, filename, content, ctype):
    boundary = "--------------" + uuid.uuid4().hex
    lines = []
    for key, values in fields.items():
        if values is None:
            continue
        if isinstance(values, str):
            values = [values]
        for v in values:
            lines.append("--" + boundary)
            lines.append('Content-Disposition: form-data; name="%s"' % key)
            lines.append("")
            lines.append(v)
    lines.append("--" + boundary)
    lines.append('Content-Disposition: form-data; name="content"; filename="%s"' % filename)
    lines.append("Content-Type: %s" % ctype)
    lines.append("")
    body = ("\r\n".join(lines) + "\r\n").encode("utf-8") + content
    body += ("\r\n--" + boundary + "--\r\n").encode("utf-8")
    return boundary, body


def main():
    sdist_path = sys.argv[1]
    with open(sdist_path, "rb") as f:
        content = f.read()

    raw, msg = pkg_info_fields(sdist_path)
    filename = os.path.basename(sdist_path)

    fields = {
        ":action": "file_upload",
        "protocol_version": "1",
        "metadata_version": msg.get("Metadata-Version"),
        "name": msg.get("Name"),
        "version": msg.get("Version"),
        "filetype": "sdist",
        "pyversion": "",
        "summary": msg.get("Summary"),
        "home_page": msg.get("Home-page"),
        "author": msg.get("Author"),
        "author_email": msg.get("Author-Email") or msg.get("Author-email"),
        "license": msg.get("License"),
        "keywords": msg.get("Keywords"),
        "platform": msg.get("Platform"),
        "classifiers": msg.get_all("Classifier"),
        "description": msg.get_payload(),
        "description_content_type": msg.get("Description-Content-Type"),
        "project_urls": msg.get_all("Project-URL"),
        "requires_python": msg.get("Requires-Python"),
    }
    fields.update(digests(content))
    fields = {k: v for k, v in fields.items() if v not in (None, "")}

    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    boundary, body = build_body(fields, filename, content, ctype)

    # Read token from ~/.pypirc [pypi] password
    pypirc = os.path.expanduser("~/.pypirc")
    token = None
    in_pypi = False
    with open(pypirc) as f:
        for line in f:
            line = line.strip()
            if line == "[pypi]":
                in_pypi = True
            elif line.startswith("["):
                in_pypi = False
            elif in_pypi and line.startswith("password"):
                token = line.split("=", 1)[1].strip()
    if not token:
        raise SystemExit("No token found in ~/.pypirc")

    req = urllib.request.Request(
        "https://upload.pypi.org/legacy/",
        data=body,
        method="POST",
        headers={
            "Content-Type": "multipart/form-data; boundary=" + boundary,
            "User-Agent": "flowsentry-stdlib-uploader/0.1 (stdlib)",
            "Authorization": "token " + token,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            print("HTTP", resp.status)
            print(resp.read().decode("utf-8", "replace")[:2000])
    except urllib.error.HTTPError as e:
        print("HTTP", e.code)
        print(e.read().decode("utf-8", "replace")[:3000])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
