# OpenChore

> Automates the boring parts of managing OpenCore EFI repositories

OpenChore is a command-line tool can:

- **downloadg** a specific version of OpenCore
- **update** the local OpenCore (and efi drivers) with the downloaded versions
- **validate** the config.plist against the new version's oc_validate
- **sign** efi drivers using provided keys for UEFI Secure Boot (optional)
- **create** the efi vault for booting with `Misc->Security->Vault` set to `Secure`

Opencore is connected to your local EFI git repository that contains your OpenCore EFI directory

# Requirements / Dependencies

1. Python 3.10 or above

- if using homebrew, you can run `brew install python3`

2. a git repository contains your EFI directory

Local EFI repository should have the `EFI` folder as a child, so the file structure should look like this:

```
.
└── example_efi_repository
    └── EFI
        ├── BOOT
        │   └── BOOTx64.efi
        └── OC
            ├── ACPI
            ├── Drivers
            ├── Kexts
            ├── OpenCore.efi
            ├── Resources
            ├── Tools
            ├── config.plist
            ├── vault.plist
            └── vault.sig
```

# Usage Instructions

- Make sure you have python 3.10 installed
- Install required python packages using `pip install wget click pathlib requests six tqdm`

For help, run `./openchore.py --help`:

```

```

## Examples

Downloading the default version and updating local efi repository (with no edits to config.plist):

```shell
./openchore.py -U -D --no-build
```
