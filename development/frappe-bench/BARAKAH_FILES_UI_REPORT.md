# Barakah Files UI Report

Date: 2026-04-25
Site used for backend verification: `development16.localhost`
Primary hosted hub: `https://selfservice.goodvanta.ge`
Secondary hosted hub checked for download: `https://selfservicetest.goodvanta.ge`

## Setup used

- `Good Connector Settings.org_id` was switched to NGO `2` for the probe
- the previous org id was restored afterward
- hosted login used the Barakah portal user `benediktmathis+playwright@gmail.com`

## Result

- Barakah file listing is working on `selfservice.goodvanta.ge`
- Barakah direct file download is working on the Frappe side
- the remaining download failure is in the hosted hub `/rest/file-urls` path
- `selfservicetest.goodvanta.ge` could not be used for download verification because token login/session auth failed there

## What was verified

### 1. Frappe-side file API

Direct local endpoint checks succeeded:

- `GetFileList` returned Barakah Well files for the portal user
- `GetFileUrls` returned `200`
- `Content-Disposition` was an attachment header
- the returned file body was non-empty HTML

Concrete example from the probe:

- file id: `28d7bf7db2`
- file name: `well-order-WE-00328.html`
- local `GetFileUrls` result: `200`, `Content-Type: HTML`, attachment header present, body size `2442`

So the Barakah app / `good_connector` backend path is working.

### 2. Hosted files listing on `selfservice.goodvanta.ge`

Hosted token login worked:

- login URL used `ngo=2`
- login redirected to `/selfservice/tasklist`

Hosted file listing also worked:

- `/rest/filelist` returned `200`
- the JSON payload contained Barakah Well HTML files
- `/selfservice/files` rendered the file names in the browser

So the previous “files UI timeout” is not reproducible right now as a stable Barakah app bug.

### 3. Hosted click/download on `selfservice.goodvanta.ge`

Clicking a file row on `/selfservice/files` did not produce a browser download, but it did fire the expected hub request:

- `GET /rest/file-urls?ids=28d7bf7db2`

The problem is the response shape from the hosted hub route:

- `/rest/file-urls?ids=28d7bf7db2` returned `200`
- response `Content-Type` was `application/json`
- body was `null`

That explains the browser behavior:

- file rows render
- click is wired
- no actual file opens/downloads because the hub URL-resolution step returns `null`

## Secondary host: `selfservicetest.goodvanta.ge`

This host is currently not usable for automated Barakah file-download verification.

Observed behavior:

- token login URL was generated successfully
- after navigating there, `/rest/session` returned `401`
- `/rest/filelist` returned `401`
- the browser ended up on `/welcome/` showing the login screen

So `selfservicetest.goodvanta.ge` is currently failing before the files route itself; it is an auth/session problem.

## Conclusion

From the Frappe side, Barakah file access is working:

- file visibility works
- direct file download works

The remaining issue is hub-side:

1. `selfservice.goodvanta.ge/rest/file-urls` needs to return a real file URL or proxy the file response instead of `null`
2. `selfservicetest.goodvanta.ge` needs working token login/session auth before it can be used as a download test target
