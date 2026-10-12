#!/usr/bin/env python3
"""Use macOS Keychain without putting secrets in command arguments or logs."""
import argparse
import ctypes
import getpass
import os
import sys


def library():
    if sys.platform != "darwin":
        raise RuntimeError("Keychain is available only on macOS; use an environment variable elsewhere")
    lib = ctypes.CDLL("/System/Library/Frameworks/Security.framework/Security")
    lib.SecKeychainFindGenericPassword.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32),
        ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_void_p)]
    lib.SecKeychainFindGenericPassword.restype = ctypes.c_int32
    lib.SecKeychainItemFreeContent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    lib.SecKeychainAddGenericPassword.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p)]
    lib.SecKeychainAddGenericPassword.restype = ctypes.c_int32
    lib.SecKeychainItemModifyAttributesAndData.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_void_p]
    lib.SecKeychainItemModifyAttributesAndData.restype = ctypes.c_int32
    core = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    core.CFRelease.argtypes = [ctypes.c_void_p]
    return lib, core


def lookup(service, account):
    lib, core = library()
    s, a = service.encode(), account.encode()
    length, data, item = ctypes.c_uint32(), ctypes.c_void_p(), ctypes.c_void_p()
    status = lib.SecKeychainFindGenericPassword(None, len(s), s, len(a), a,
                                               ctypes.byref(length), ctypes.byref(data), ctypes.byref(item))
    if status == -25300:
        return None
    if status != 0:
        raise RuntimeError(f"Keychain read failed (OSStatus {status})")
    try:
        return ctypes.string_at(data, length.value).decode()
    finally:
        lib.SecKeychainItemFreeContent(None, data)
        if item.value:
            core.CFRelease(item)


def save(service, account, secret):
    if not secret or any(c.isspace() for c in secret):
        raise ValueError("Expected one non-empty credential without whitespace")
    lib, core = library()
    s, a, value = service.encode(), account.encode(), secret.encode()
    item = ctypes.c_void_p()
    status = lib.SecKeychainFindGenericPassword(None, len(s), s, len(a), a, None, None, ctypes.byref(item))
    try:
        if status == -25300:
            status = lib.SecKeychainAddGenericPassword(None, len(s), s, len(a), a,
                                                      len(value), value, ctypes.byref(item))
        elif status == 0:
            status = lib.SecKeychainItemModifyAttributesAndData(item, None, len(value), value)
        if status != 0:
            raise RuntimeError(f"Keychain write failed (OSStatus {status})")
    finally:
        if item.value:
            core.CFRelease(item)


def resolve(profile):
    name = profile.get("api_key_env", "FISH_API_KEY")
    if os.environ.get(name):
        return os.environ[name]
    config = profile.get("keychain")
    if config and sys.platform == "darwin":
        value = lookup(config["service"], config["account"])
        if value:
            return value
    raise RuntimeError(f"Credential unavailable: {name} or configured Keychain item")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["status", "set"])
    parser.add_argument("--service", required=True)
    parser.add_argument("--account", required=True)
    parser.add_argument("--stdin", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "status":
            print("available" if lookup(args.service, args.account) else "missing")
        else:
            value = sys.stdin.read().strip() if args.stdin else getpass.getpass("API key (hidden): ")
            save(args.service, args.account, value)
            print("saved_to_keychain")
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
