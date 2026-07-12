# Security Policy

## Supported versions

Only the [latest release](https://github.com/abrahao-dev/auris/releases/latest)
receives fixes.

## Auris's security model

Auris is a passive BLE listener: it never pairs, connects, writes, or sends
data anywhere. It reads public advertisements that nearby Apple/Beats earbuds
already broadcast in the clear. Settings are stored in a local JSON file; there
is no network code and no telemetry.

Relevant reports therefore include things like:

- Code execution triggered by a crafted BLE advertisement (decoder parsing bugs)
- Privilege or permission issues in the installer / autostart integration
- Supply-chain issues in the build or release pipeline

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Instead:

- Use GitHub's [private vulnerability reporting](https://github.com/abrahao-dev/auris/security/advisories/new), or
- Email **contato.matheusabrahao@gmail.com**

Include reproduction steps and, for decoder bugs, the raw advertisement bytes.
You can expect an acknowledgment within a week. Fixes are released as fast as a
hobby project allows, with credit to the reporter unless you prefer otherwise.
