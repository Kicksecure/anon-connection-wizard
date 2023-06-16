# Tor Connection Configuration (ACW) #

WARNING: Not (yet) a standalone ready to use outside of Whonix:

Creates a Tor settings file:
`/usr/local/etc/torrc.d/40_tor_control_panel.conf`

anon-connection-wizard (ACW) is a Tor-launcher-like application that helps
users in different Internet environment connect to the Tor network.
It helps user to configure Tor to use a proxy and/or Tor bridges.
This application is especially useful for system Tor users who would like
to run the standalone core Tor with different torified applications.
The wizard can be run at any time to change the connection configuration.

Creates a Tor settings file:
`/usr/local/etc/torrc.d/40_tor_control_panel.conf`

anon-connection-wizard is produced independently from the Tor anonymity
software and carries no guarantee from The Tor Project about quality,
suitability or anything else.

## How to install `anon-connection-wizard` using apt-get ##

1\. Download the APT Signing Key.

```
wget https://www.kicksecure.com/keys/derivative.asc
```

Users can [check the Signing Key](https://www.kicksecure.com/wiki/Signing_Key) for better security.

2\. Add the APT Signing Key.

```
sudo cp ~/derivative.asc /usr/share/keyrings/derivative.asc
```

3\. Add the derivative repository.

```
echo "deb [signed-by=/usr/share/keyrings/derivative.asc] https://deb.kicksecure.com bookworm main contrib non-free" | sudo tee /etc/apt/sources.list.d/derivative.list
```

4\. Update your package lists.

```
sudo apt-get update
```

5\. Install `anon-connection-wizard`.

```
sudo apt-get install anon-connection-wizard
```

## How to Build deb Package from Source Code ##

Can be build using standard Debian package build tools such as:

```
dpkg-buildpackage -b
```

See instructions.

NOTE: Replace `generic-package` with the actual name of this package `anon-connection-wizard`.

* **A)** [easy](https://www.kicksecure.com/wiki/Dev/Build_Documentation/generic-package/easy), _OR_
* **B)** [including verifying software signatures](https://www.kicksecure.com/wiki/Dev/Build_Documentation/generic-package)

## Contact ##

* [Free Forum Support](https://forums.kicksecure.com)
* [Premium Support](https://www.kicksecure.com/wiki/Premium_Support)

## Donate ##

`anon-connection-wizard` requires [donations](https://www.kicksecure.com/wiki/Donate) to stay alive!
