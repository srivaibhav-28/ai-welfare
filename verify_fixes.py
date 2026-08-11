import urllib.request, json, sys

BASE = "http://127.0.0.1:8000"
results = []

def check(label, value, expected=True):
    status = "PASS" if value == expected else "FAIL"
    results.append((status, label))
    print(f"[{status}] {label}")

try:
    # 1. Server up
    code = urllib.request.urlopen(f"{BASE}/").getcode()
    check("Server returns HTTP 200", code == 200)

    # 2. HTML checks
    html = urllib.request.urlopen(f"{BASE}/").read().decode("utf-8")
    check("Script v=10.0 in HTML", "app.js?v=10.0" in html)
    check("appOtpModal has no flex+hidden conflict", "z-[9999] flex items" not in html)
    check("appOtpModal has display:none inline style", 'style="z-index:99999;display:none;"' in html)

    # 3. JS checks
    js = urllib.request.urlopen(f"{BASE}/static/js/app.js?v=10.0").read().decode("utf-8")
    check("JS has backdropFilter (blur overlay)", "backdropFilter" in js)
    check("JS 123456 backdoor removed", "123456" not in js)
    check("JS openAppOtpModal exists", "function openAppOtpModal" in js)
    check("JS submitAppOtpVerification exists", "function submitAppOtpVerification" in js)
    check("JS handleResendAppOtp exists", "function handleResendAppOtp" in js)
    check("JS window.openAppOtpModal assigned", "window.openAppOtpModal = openAppOtpModal" in js)

    # 4. Backend checks
    py_file = open("api/applications.py").read()
    check("Backend uses secrets (not random)", "import secrets" in py_file and "import random" not in py_file)
    check("Backend OTP not logged to console", "OTP Generation: {otp_code}" not in py_file)
    check("Backend 123456 backdoor removed", 'clean_code != "123456"' not in py_file)
    check("Backend uses secrets.randbelow", "secrets.randbelow" in py_file)

    # 5. API endpoint: initiate-otp response must NOT include otp field
    # Test with fixture credentials
    req_data = json.dumps({"scheme_id": "scheme-001", "uploaded_documents": {
        "Aadhaar Card": "a.jpg",
        "Land Ownership Document (Khatauni/Khasra)": "b.jpg",
        "Active Bank Passbook": "c.jpg",
        "Residence Certificate": "d.jpg"
    }}).encode()
    req = urllib.request.Request(
        f"{BASE}/api/applications/initiate-otp",
        data=req_data,
        headers={"Content-Type": "application/json", "Authorization": "Bearer usr-g-test"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req)
        body = json.loads(resp.read())
        check("initiate-otp returns HTTP 200", True)
        check("initiate-otp response does NOT contain 'otp' key", "otp" not in body)
        check("initiate-otp response contains status=otp_sent", body.get("status") == "otp_sent")
    except urllib.request.HTTPError as e:
        err = json.loads(e.read())
        check(f"initiate-otp HTTP {e.code}: {err.get('detail','')}", False)

    # 6. verify-otp with wrong code must return 400
    verify_data = json.dumps({"scheme_id": "scheme-001", "otp": "000000", "uploaded_documents": {}}).encode()
    req2 = urllib.request.Request(
        f"{BASE}/api/applications/verify-submit-otp",
        data=verify_data,
        headers={"Content-Type": "application/json", "Authorization": "Bearer usr-g-test"},
        method="POST"
    )
    try:
        resp2 = urllib.request.urlopen(req2)
        check("Wrong OTP rejected (should not reach here)", False)
    except urllib.request.HTTPError as e:
        check("Wrong OTP returns HTTP 400 (rejected)", e.code == 400)

    # 7. verify-otp with 123456 must now FAIL (backdoor removed)
    verify_backdoor = json.dumps({"scheme_id": "scheme-001", "otp": "123456", "uploaded_documents": {}}).encode()
    req3 = urllib.request.Request(
        f"{BASE}/api/applications/verify-submit-otp",
        data=verify_backdoor,
        headers={"Content-Type": "application/json", "Authorization": "Bearer usr-g-test"},
        method="POST"
    )
    try:
        resp3 = urllib.request.urlopen(req3)
        check("Backdoor OTP 123456 accepted (BAD - backdoor still active)", False)
    except urllib.request.HTTPError as e:
        check("Backdoor OTP 123456 correctly rejected (backdoor removed)", e.code == 400)

except Exception as ex:
    print(f"[ERROR] Unexpected exception: {ex}")
    sys.exit(1)

passed = sum(1 for s,_ in results if s == "PASS")
failed = sum(1 for s,_ in results if s == "FAIL")
print(f"\n{'='*60}")
print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {len(results)} checks")
if failed == 0:
    print("ALL CHECKS PASSED")
else:
    sys.exit(1)
