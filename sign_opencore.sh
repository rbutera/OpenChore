#!/bin/bash
# Copyright (c) 2021 by profzei
# Licensed under the terms of the GPL v3

# OpenCore download link
# LINK=$1
# https://github.com/acidanthera/OpenCorePkg/releases/download/0.7.5/OpenCore-0.7.5-RELEASE.zip
# VERSION=$2
# 0.7.5 current

# Terminal command in Linux
# sh ./sign_opencore.sh https://github.com/acidanthera/OpenCorePkg/releases/download/0.7.5/OpenCore-0.7.5-RELEASE.zip 0.7.5

echo "==============================="
echo "Creating required directories"
mkdir -p signed
mkdir -p signed/Drivers
mkdir -p signed/Tools
mkdir -p signed/Download
mkdir -p signed/BOOT
mkdir -p signed/OC
# echo "==============================="
# echo Downloading HfsPlus
# wget -nv https://github.com/acidanthera/OcBinaryData/raw/master/Drivers/HfsPlus.efi -O ./signed/Download/HfsPlus.efi
# #echo "==============================="
# # uncomment the next 2 lines if you use OpenLinuxBoot
# #echo Downloading ext4_x64.efi
# #wget -nv https://github.com/acidanthera/OcBinaryData/raw/master/Drivers/ext4_x64.efi -O ./signed/Download/ext4_x64.efi
# echo "==============================="
# echo Downloading and unziping OpenCore
# wget -nv $LINK
# unzip "OpenCore-${VERSION}-RELEASE.zip" "X64/*" -d "./signed/Download"
# echo "==============================="
# # If you don't want to delete downloaded OpenCore zip file, comment next line
# rm "OpenCore-${VERSION}-RELEASE.zip"
echo "==============================="
echo "Checking ISK files"
if [ -f "./keys/ISK.key" ]; then
    echo "ISK.key was decrypted successfully"
fi

if [ -f "./keys/ISK.pem" ]; then
    echo "ISK.pem was decrypted successfully"
fi
echo "==============================="
echo "Signing drivers, tools, BOOTx64.efi and OpenCore.efi"
sleep 2
# You can modify drivers and tools to be signed to your like
echo ""
cp -Rv ./EFI/* ./signed/
rm -rf ./signed/BOOT/BOOTx64.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/BOOT/BOOTx64.efi ./EFI/BOOT/BOOTx64.efi
rm -rf ./signed/OC/OpenCore.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/OpenCore.efi ./EFI/OC/OpenCore.efi
rm -rf ./signed/OC/Drivers/OpenRuntime.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Drivers/OpenRuntime.efi ./EFI/OC/Drivers/OpenRuntime.efi
rm -rf ./signed/OC/Drivers/OpenCanopy.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Drivers/OpenCanopy.efi ./EFI/OC/Drivers/OpenCanopy.efi
rm -rf ./signed/OC/Drivers/ResetNvramEntry.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Drivers/ResetNvramEntry.efi ./EFI/OC/Drivers/OpenCanopy.efi
rm -rf ./signed/OC/Drivers/HfsPlus.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Drivers/HfsPlus.efi ./EFI/OC/Drivers/HfsPlus.efi
rm -rf ./signed/OC/Tools/CFGLock.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Tools/CFGLock.efi ./EFI/OC/Tools/CFGLock.efi
rm -rf ./signed/OC/Tools/CleanNvram.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Tools/CleanNvram.efi ./EFI/OC/Tools/CleanNvram.efi
rm -rf ./signed/OC/Tools/ControlMsrE2.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Tools/ControlMsrE2.efi ./EFI/OC/Tools/ControlMsrE2.efi
rm -rf ./signed/OC/Tools/OpenShell.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Tools/OpenShell.efi ./EFI/OC/Tools/OpenShell.efi
rm -rf ./signed/OC/Tools/ResetSystem.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Tools/ResetSystem.efi ./EFI/OC/Tools/ResetSystem.efi
rm -rf ./signed/OC/Tools/VerifyMsrE2.efi
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/OC/Tools/VerifyMsrE2.efi ./EFI/OC/Tools/VerifyMsrE2.efi

# You can sign also keytool to boot from USB with UEFI Secure Boot enabled
sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/KeyTool.efi ./KeyTool.efi

# uncomment the next 2 lines if you use OpenLinuxBoot
#sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/Drivers/OpenLinuxBoot.efi ./EFI/OC/Drivers/OpenLinuxBoot.efi
#sbsign --key ./keys/ISK.key --cert ./keys/ISK.pem --output ./signed/Drivers/ext4_x64.efi ./signed/Download/ext4_x64.efi
echo "==============================="
# Clean: remove downloaded files

echo "verifying"
sbverify --list ./signed/BOOT/BOOTx64.efi
