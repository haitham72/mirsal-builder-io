# HTTPS for the office network

`python -m mirsal serve --lan` uses HTTPS, so passwords and sign-in cookies never cross the Wi-Fi in clear. You do this once.

## 1. On the PC that runs Mirsal

macOS:

```
brew install mkcert
mkcert -install
```

Windows (PowerShell as administrator): `choco install mkcert`, then `mkcert -install`.

Find this PC's address on the office network (macOS: `ipconfig getifaddr en0`; Windows: `ipconfig`, "IPv4 Address"), then, from the repository root:

```
mkcert -cert-file mirsal/out/tls/cert.pem -key-file mirsal/out/tls/key.pem 192.168.1.66 localhost
```

Replace `192.168.1.66` with your address. Start Mirsal:

```
cd mirsal
venv/bin/python -m mirsal serve --lan
```

It prints the address colleagues open, for example `https://192.168.1.66:8770`.

## 2. On each office machine (once)

They must trust **this PC's** certificate authority (not their own: do not run `mkcert -install` there).

1. On the Mirsal PC, run `mkcert -CAROOT` and copy `rootCA.pem` from that folder to the colleague's machine (USB, shared drive). Never copy `rootCA-key.pem`.
2. Install it:
   - **macOS:** double-click `rootCA.pem` → Keychain Access → open the certificate → Trust → **Always Trust**.
   - **Windows:** double-click `rootCA.pem` → Install Certificate → Local Machine → **Trusted Root Certification Authorities**.
3. Open the address Mirsal printed. No warning appears; they sign up with their `@nadi.ae` email and wait for your approval.

## When something changes

- **The PC's address changes:** run the `mkcert -cert-file …` line again with the new address and restart Mirsal. The office machines keep working (they trust the authority, not the address).
- **A browser warns "not private":** that machine has not trusted `rootCA.pem` yet (step 2).
- **Without a certificate:** `serve --lan --no-tls` runs plain HTTP and warns on start; passwords can then be read on the network.

`mirsal/out/tls/` is git-ignored: the certificate and key never go to git. Keep `rootCA-key.pem` on the Mirsal PC only.
