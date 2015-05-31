#! /bin/sh

gen_private_key() {
	openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:2048 -pkeyopt rsa_keygen_pubexp:3 -out ./certificate/carbono.pem
}

gen_certificate_request() {
	openssl req -new -key ./certificate/carbono.pem -out ./certificate/carbono.csr
}

sign_certificate() {
	openssl x509 -req -days 365 -in ./certificate/carbono.csr -signkey ./certificate/carbono.pem -out ./certificate/carbono.crt
}

main() {
	mkdir ./certificate
	gen_private_key
	gen_certificate_request
	sign_certificate
}

main
