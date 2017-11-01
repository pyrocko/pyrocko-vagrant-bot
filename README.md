# pyrocko-vagrant-webhook


## Installation

```
sudo python3 setup.py install
```

## Initialize a New Config File

```
pyrocko-vagrant-bot init filename.yml
```

## Create SSL Certificate

```
$ openssl genrsa -des3 -passout pass:x -out server.pass.key 2048
...
$ openssl rsa -passin pass:x -in server.pass.key -out server.key
writing RSA key
$ rm server.pass.key
$ openssl req -new -key server.key -out server.csr
...
Country Name (2 letter code) [AU]:US
State or Province Name (full name) [Some-State]:California
...
A challenge password []:
...

```

## Start the Server

```
pyrocko-vagrant-bot serve filename.yml
```


## Test the Hook

Start the server and run

```
pyrocko-vagrant-bot request filename.yml
```
