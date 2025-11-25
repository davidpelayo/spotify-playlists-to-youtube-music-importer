#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for local HTTPS development.
Required for Spotify OAuth callbacks which must use HTTPS.
"""
import os
from OpenSSL import crypto
import socket


def generate_self_signed_cert(cert_file='cert.pem', key_file='key.pem'):
    """
    Generate a self-signed SSL certificate for localhost.
    
    Args:
        cert_file: Path to save certificate file
        key_file: Path to save private key file
    """
    # Create a key pair
    print("Generating RSA key pair...")
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    
    # Create a self-signed cert
    print("Creating self-signed certificate...")
    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "State"
    cert.get_subject().L = "City"
    cert.get_subject().O = "Playlist Migrator"
    cert.get_subject().OU = "Development"
    cert.get_subject().CN = "localhost"
    
    # Add Subject Alternative Names for localhost and custom domain
    cert.add_extensions([
        crypto.X509Extension(
            b"subjectAltName",
            False,
            b"DNS:localhost,DNS:playlists.migrator,IP:127.0.0.1"
        )
    ])
    
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365 * 24 * 60 * 60)  # Valid for 1 year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')
    
    # Save certificate
    print(f"Saving certificate to {cert_file}...")
    with open(cert_file, "wb") as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    
    # Save private key
    print(f"Saving private key to {key_file}...")
    with open(key_file, "wb") as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    
    print("\n✅ SSL certificates generated successfully!")
    print(f"   Certificate: {cert_file}")
    print(f"   Private Key: {key_file}")
    print("\n⚠️  Note: This is a self-signed certificate for development only.")
    print("   Your browser will show a security warning - this is expected.")
    print("   Click 'Advanced' and 'Proceed to localhost' to continue.\n")


if __name__ == '__main__':
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.join(script_dir, 'cert.pem')
    key_path = os.path.join(script_dir, 'key.pem')
    
    # Check if certificates already exist
    if os.path.exists(cert_path) and os.path.exists(key_path):
        response = input("SSL certificates already exist. Regenerate? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing certificates.")
            exit(0)
    
    generate_self_signed_cert(cert_path, key_path)
