#!/usr/bin/python
"""
    androidcrypt.py allows access to Android's encrypted partitions from a
    recovery image.
    Copyright (C) 2012 Michael Zugelder

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import binascii
import os
import struct

class ValidationException(Exception):
    pass

class CryptFooter():

    CRYPT_MNT_MAGIC = 0xD0B5B1C4
    EXPECTED_FOOTER_SIZE = 100 # sizeof(struct crypt_mnt_ftr)
    KEY_TO_SALT_PADDING = 32
    SALT_LEN = 16

    def __init__(self, f):
        self.magic = self.read_magic(f)
        self.major_version = self.read_major_version(f)
        self.minor_version = self.read_minor_version(f)
        self.ftr_size = self.read_ftr_size(f)
        self.flags = self.read_flags(f)
        self.keysize = self.read_keysize(f)
        self.spare1 = self.read_spare1(f)
        self.fs_size = self.read_fs_size(f)
        self.failed_decrypt_count = self.read_failed_decrypt_count(f)
        self.crypt_type_name = self.read_crypt_type_name(f)
        self.encrypted_master_key = self.read_encrypted_master_key(f)
        self.salt = self.read_salt(f)
        self.scrypt_N = self.read_scrypt_N(f)
        self.scrypt_r = self.read_scrypt_r(f)
        self.scrypt_p = self.read_scrypt_p(f)

    def read_magic(self, f):
        magic = self.read_le32(f)
        if magic != self.CRYPT_MNT_MAGIC:
            raise ValidationException(
                "Invalid magic value, expected 0x%X, got 0x%X."
                % (self.CRYPT_MNT_MAGIC, magic))
        return magic

    def read_major_version(self, f):
        major_version = self.read_le16(f)
        if major_version != 1:
            raise ValidationException(
                'Unsupported crypto footer major version, expected 1, got %d.'
                % major_version)
        return major_version

    def read_minor_version(self, f):        return self.read_le16(f)
    def read_ftr_size(self, f):             return self.read_le32(f)
    def read_flags(self, f):                return self.read_le32(f)
    def read_keysize(self, f):              return self.read_le32(f)
    def read_spare1(self, f):               return self.read_le32(f)
    def read_fs_size(self, f):              return self.read_le64(f)
    def read_failed_decrypt_count(self, f): return self.read_le32(f)
    def read_crypt_type_name(self, f):      return f.read(64).rstrip('\0')

    def read_encrypted_master_key(self, f):
        #if self.ftr_size > self.EXPECTED_FOOTER_SIZE :
            # skip to the end of the footer if it's bigger than expected
            #f.seek(self.ftr_size - self.EXPECTED_FOOTER_SIZE, os.SEEK_CUR)
        # skip spare2
        f.seek(4, os.SEEK_CUR)
        return f.read(self.keysize)

    def read_salt(self, f):
        f.seek(self.KEY_TO_SALT_PADDING, os.SEEK_CUR)
        return f.read(self.SALT_LEN)

    def read_scrypt_N(self, f):
        # Skip persist data stuff and KDF
        f.seek(8 + 8 + 4 + 1, os.SEEK_CUR)
        return 2 ** ord(f.read(1))
    def read_scrypt_r(self, f): return 2 ** ord(f.read(1))
    def read_scrypt_p(self, f): return 2 ** ord(f.read(1))

    # Utility functions
    def read_le16(self, f):
        return struct.unpack('<H', f.read(2))[0] # unsigned short

    def read_le32(self, f):
        return struct.unpack('<I', f.read(4))[0] # unsigned {int,long}

    def read_le64(self, f):
        return struct.unpack('<Q', f.read(8))[0] # unsigned long ong

    def __str__(self):
        return ("CryptFooter { magic=0x%X, major_version=%d, " + \
               "minor_version=%d, ftr_size=%d, flags=0x%X, keysize=%d, " + \
               "spare1=0x%X, fs_size=%d, failed_decrypt_count=%d, " + \
               "crypt_type_name=\"%s\", encrypted_master_key=0x%s, " + \
               "salt=0x%s, N=%d, r=%d, p=%d }") \
               % (self.magic, self.major_version, self.minor_version,
                  self.ftr_size, self.flags, self.keysize, self.spare1,
                  self.fs_size, self.failed_decrypt_count,
                  self.crypt_type_name,
                  binascii.hexlify(self.encrypted_master_key),
                  binascii.hexlify(self.salt), self.scrypt_N, self.scrypt_r, self.scrypt_p)
