# Tor Connection Configuration #

anon-connection-wizard is a Tor-launcher-like application that helps users
in different Internet environment connect to the Tor network. It helps user
to configure Tor to use a proxy and/or Tor bridges. This application is
especially useful for system Tor users who would like to run the standalone
core Tor with different torified applications. The wizard can be run at any
time to change the connection configuration.

anon-connection-wizard is produced independently from the Tor anonymity
software and carries no guarantee from The Tor Project about quality,
suitability or anything else.
## How to install `anon-connection-wizard` using apt-get ##

1\. Add [Whonix's Signing Key](https://www.whonix.org/wiki/Whonix_Signing_Key).

```
sudo apt-key --keyring /etc/apt/trusted.gpg.d/whonix.gpg adv --keyserver hkp://ipv4.pool.sks-keyservers.net:80 --recv-keys 916B8D99C38EAF5E8ADC7A2A8D66066A2EEACCDA
```

3\. Add Whonix's APT repository.

```
echo "deb http://deb.whonix.org stretch main" | sudo tee /etc/apt/sources.list.d/whonix.list
```

4\. Update your package lists.

```
sudo apt-get update
```

5\. Install `anon-connection-wizard`.

```
sudo apt-get install anon-connection-wizard
```

## How to Build deb Package ##

Replace `apparmor-profile-torbrowser` with the actual name of this package with `anon-connection-wizard` and see [instructions](https://www.whonix.org/wiki/Dev/Build_Documentation/apparmor-profile-torbrowser).

## Contact ##

* [Free Forum Support](https://forums.whonix.org)
* [Professional Support](https://www.whonix.org/wiki/Professional_Support)

## Payments ##

`anon-connection-wizard` requires [payments](https://www.whonix.org/wiki/Payments) to stay alive!
