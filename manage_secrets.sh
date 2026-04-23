#!/bin/bash

# Configuration
KEY_DIR="./.keys"
AGE_KEY_FILE="$KEY_DIR/key.txt"
SOPS_CONFIG=".sops.yaml"
export SOPS_AGE_KEY_FILE="$AGE_KEY_FILE"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

mkdir -p "$KEY_DIR"
[[ ! -f .gitignore ]] || grep -q ".keys/" .gitignore || echo ".keys/" >> .gitignore

show_menu() {
    echo -e "\n${BLUE}--- Universal SOPS Vault ---${NC}"
    echo "1) Setup (Install & Generate Key)"
    echo "2) Encrypt a New File (Adds .sops)"
    echo "3) Open/Edit a File (Decrypt -> Use -> Re-encrypt)"
    echo "4) Decrypt All .sops Files"
    echo "5) Re-encrypt All Decrypted .sops Files"
    echo "6) Add Coworker to Vault"
    echo "7) Remove Coworker from Vault"
    echo "8) Rotate Key and Re-encrypt All Files"
    echo "9) Exit"
    echo "----------------------------"
}

# Helper to find files
select_file() {
    local ext=$1
    FILES=($(ls *$ext 2>/dev/null | grep -v "manage_secrets.sh" | grep -v ".sops.yaml"))
    if [ ${#FILES[@]} -eq 0 ]; then
        echo -e "${RED}No files found with extension $ext${NC}"
        return 1
    fi
    echo "Select a file:"
    for i in "${!FILES[@]}"; do echo "$i) ${FILES[$i]}"; done
    read -p "Choice: " idx
    SELECTED_FILE="${FILES[$idx]}"
}

encrypt_new() {
    # If a filename argument is passed, use it directly bypassing the interactive menu
    if [ -n "$1" ]; then
        SELECTED_FILE="$1"
        if [ ! -f "$SELECTED_FILE" ]; then
            echo -e "${RED}File $SELECTED_FILE not found!${NC}"
            return 1
        fi
    else
        select_file "" # List all files interactively
        [ $? -eq 0 ] || return 1
    fi

    if sops --encrypt --input-type binary --output-type binary --output "$SELECTED_FILE.sops" "$SELECTED_FILE"; then
        rm "$SELECTED_FILE" # Remove original unencrypted file
        echo -e "${GREEN}Encrypted as $SELECTED_FILE.sops and original removed.${NC}"
    else
        echo -e "${RED}Encryption failed! Original file kept.${NC}"
        return 1
    fi
}

use_file() {
    select_file ".sops"
    if [ $? -eq 0 ]; then
        # Create temp filename by removing .sops
        TEMP_FILE="${SELECTED_FILE%.sops}"
        
        echo -e "${BLUE}Decrypting $SELECTED_FILE for use...${NC}"
        sops --decrypt --input-type binary --output-type binary --output "$TEMP_FILE" "$SELECTED_FILE"
        
        echo -e "${GREEN}File is now available at: $TEMP_FILE${NC}"
        echo "The script is waiting. Edit the file or use it now."
        read -p "Press [Enter] when finished to re-encrypt and secure..." 

        # Re-encrypt and clean up
        sops --encrypt --input-type binary --output-type binary --output "$SELECTED_FILE" "$TEMP_FILE"
        
        # Securely remove the unencrypted file
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            shred -u "$TEMP_FILE" # Secure overwrite for WSL/Linux
        else
            rm "$TEMP_FILE"
        fi
        
        echo -e "${GREEN}File $SELECTED_FILE updated. Unencrypted version wiped.${NC}"
    fi
}

decrypt_all() {
    echo -e "${BLUE}Decrypting all .sops files...${NC}"
    local found=0
    for file in *.sops; do
        if [ -f "$file" ]; then
            found=1
            TEMP_FILE="${file%.sops}"
            sops --decrypt --input-type binary --output-type binary --output "$TEMP_FILE" "$file"
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Decrypted $file to $TEMP_FILE${NC}"
            else
                echo -e "${RED}Failed to decrypt $file${NC}"
            fi
        fi
    done
    if [ $found -eq 0 ]; then
        echo -e "${RED}No .sops files found to decrypt.${NC}"
    fi
}

encrypt_all() {
    echo -e "${BLUE}Encrypting all previously decrypted files...${NC}"
    local found=0
    for file in *.sops; do
        if [ -f "$file" ]; then
            TEMP_FILE="${file%.sops}"
            if [ -f "$TEMP_FILE" ]; then
                found=1
                sops --encrypt --input-type binary --output-type binary --output "$file" "$TEMP_FILE"
                if [ $? -eq 0 ]; then
                    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                        shred -u "$TEMP_FILE" # Secure overwrite for WSL/Linux
                    else
                        rm "$TEMP_FILE"
                    fi
                    echo -e "${GREEN}Re-encrypted and securely removed $TEMP_FILE${NC}"
                else
                    echo -e "${RED}Failed to re-encrypt $TEMP_FILE${NC}"
                fi
            fi
        fi
    done
    if [ $found -eq 0 ]; then
        echo -e "${RED}No unencrypted files found that match existing .sops files.${NC}"
    fi
}

rotate_key() {
    echo -e "${BLUE}Starting key rotation...${NC}"
    
    # 1. Pre-validation: check that ALL files can be decrypted before proceeding
    local failed=0
    for file in *.sops; do
        # Check if there are no matches
        [ -e "$file" ] || continue
        # Quickly test decryption to /dev/null
        if ! sops --decrypt "$file" &>/dev/null; then
            echo -e "${RED}Error: Cannot decrypt $file. Aborting rotation to prevent unrecoverable state.${NC}"
            failed=1
        fi
    done
    
    if [ $failed -eq 1 ]; then
        echo -e "${RED}Key rotation aborted due to decryption failures. No keys were changed.${NC}"
        return 1
    fi
    
    # 2. Setup a secure temporary directory
    local temp_dir=$(mktemp -d)
    # Ensure cleanup on exit or interrupt, preserving security
    trap 'rm -rf "$temp_dir"' EXIT INT TERM
    
    # 3. Decrypt all files to the secure temp directory
    local found=0
    for file in *.sops; do
        [ -e "$file" ] || continue
        found=1
        local temp_file="$temp_dir/${file%.sops}"
        if ! sops --decrypt --input-type binary --output-type binary --output "$temp_file" "$file"; then
             echo -e "${RED}Critical Error: Failed to decrypt $file during rotation! Aborting.${NC}"
             return 1
        fi
    done
    
    if [ $found -eq 0 ]; then
        echo -e "${RED}No .sops files found to rotate.${NC}"
        return 0
    fi
    
    # 4. Backup old key and create new one
    echo -e "${BLUE}Generating new age key...${NC}"
    local OLD_PUB=""
    if [ -f "$AGE_KEY_FILE" ]; then
        OLD_PUB=$(grep -oP 'public key: \K.*' "$AGE_KEY_FILE")
        local BACKUP_KEY="${AGE_KEY_FILE}.bak_$(date +%s)"
        mv "$AGE_KEY_FILE" "$BACKUP_KEY"
        echo -e "${GREEN}Backed up old key to $BACKUP_KEY${NC}"
    fi
    age-keygen -o "$AGE_KEY_FILE"
    
    # 5. Update SOPS config
    local NEW_PUB=$(grep -oP 'public key: \K.*' "$AGE_KEY_FILE")
    if [ -n "$OLD_PUB" ] && [ -f "$SOPS_CONFIG" ] && grep -q "$OLD_PUB" "$SOPS_CONFIG"; then
        # Safely replace only our old key with the new key, preserving coworkers
        sed -i "s/$OLD_PUB/$NEW_PUB/" "$SOPS_CONFIG"
        echo -e "${GREEN}SOPS config updated. Replaced old key with new public key: $NEW_PUB${NC}"
    else
        echo "creation_rules: [{path_regex: '.*', age: '$NEW_PUB'}]" > "$SOPS_CONFIG"
        echo -e "${GREEN}SOPS config generated with new public key: $NEW_PUB${NC}"
    fi
    
    # 6. Re-encrypt all files from the safe temp directory
    for file in *.sops; do
        [ -e "$file" ] || continue
        local temp_file="$temp_dir/${file%.sops}"
        if sops --encrypt --input-type binary --output-type binary --output "$file" "$temp_file"; then
            echo -e "${GREEN}Re-encrypted $file with new key.${NC}"
        else
            echo -e "${RED}Failed to re-encrypt $file. The unencrypted version is kept in $temp_dir for safety.${NC}"
            # Cancel trap to preserve the temp dir so the user can manually recover
            trap - EXIT INT TERM
        fi
    done
    
    # Cleanup temp dir manually
    rm -rf "$temp_dir"
    trap - EXIT INT TERM
    echo -e "${GREEN}Key rotation successfully completed!${NC}"
}

sync_sops_files() {
    echo -e "${BLUE}Automating re-encryption to apply rules to existing files...${NC}"
    local found=0
    for file in *.sops; do
        [ -e "$file" ] || continue
        found=1
        
        # sops updatekeys safely updates the keys associated with a file based on .sops.yaml rules
        if sops updatekeys -y "$file" &>/dev/null; then
             echo -e "${GREEN}Successfully updated keys for $file${NC}"
        else
             # Fallback if updatekeys fails
             echo -e "${RED}Failed to update keys for $file with 'updatekeys'. Trying decrypt/encrypt fallback...${NC}"
             local TEMP_FILE="${file%.sops}"
             if sops --decrypt --input-type binary --output-type binary --output "$TEMP_FILE" "$file"; then
                 if sops --encrypt --input-type binary --output-type binary --output "$file" "$TEMP_FILE"; then
                     if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                         shred -u "$TEMP_FILE"
                     else
                         rm "$TEMP_FILE"
                     fi
                     echo -e "${GREEN}Re-encrypted $file${NC}"
                 else
                     echo -e "${RED}Error re-encrypting $file${NC}"
                 fi
             else
                 echo -e "${RED}Error decrypting $file${NC}"
             fi
        fi
    done
    
    if [ $found -eq 0 ]; then
        echo -e "${RED}No .sops files found to update.${NC}"
    fi
}

add_coworker() {
    read -p "Paste Key: " K
    if [ -z "$K" ]; then
        echo -e "${RED}No key provided. Aborting.${NC}"
        return 1
    fi
    
    # Add key to SOPS_CONFIG
    sed -i "s/age: '/age: '$K,/" "$SOPS_CONFIG"
    echo -e "${GREEN}Key added to $SOPS_CONFIG${NC}"
    
    sync_sops_files
    echo -e "${GREEN}Coworker successfully added to vault!${NC}"
}

remove_coworker() {
    read -p "Paste Key to Remove: " K
    if [ -z "$K" ]; then
        echo -e "${RED}No key provided. Aborting.${NC}"
        return 1
    fi
    
    # Check if they are trying to remove their own key
    local MY_PUB=""
    if [ -f "$AGE_KEY_FILE" ]; then
        MY_PUB=$(grep -oP 'public key: \K.*' "$AGE_KEY_FILE")
        if [ "$K" == "$MY_PUB" ]; then
            echo -e "${RED}You cannot remove your own key! Aborting.${NC}"
            return 1
        fi
    fi
    
    # Check if key exists in config
    if ! grep -q "$K" "$SOPS_CONFIG"; then
        echo -e "${RED}Key not found in $SOPS_CONFIG. Aborting.${NC}"
        return 1
    fi

    # Remove key from SOPS_CONFIG (handling commas properly)
    sed -i "s/$K,//g; s/,$K//g; s/$K//g" "$SOPS_CONFIG"
    echo -e "${GREEN}Key removed from $SOPS_CONFIG${NC}"
    
    sync_sops_files
    echo -e "${GREEN}Coworker successfully removed from vault!${NC}"
}

# --- Standard Logic ---
install_all() {
    sudo apt update && sudo apt install -y age curl
    VERSION=$(curl -s "https://api.github.com/repos/getsops/sops/releases/latest" | grep -Po '"tag_name": "v\K[0-9.]+')
    curl -LO "https://github.com/getsops/sops/releases/download/v${VERSION}/sops-v${VERSION}.linux.amd64"
    sudo mv sops-v${VERSION}.linux.amd64 /usr/local/bin/sops && sudo chmod +x /usr/local/bin/sops
    [ ! -f "$AGE_KEY_FILE" ] && age-keygen -o "$AGE_KEY_FILE"
    PUB=$(grep -oP 'public key: \K.*' "$AGE_KEY_FILE")
    echo "creation_rules: [{path_regex: '.*', age: '$PUB'}]" > "$SOPS_CONFIG"
    echo -e "${GREEN}Environment ready with key: $PUB${NC}"
}

# --- Non-interactive CLI Argument Handling ---
if [ "$1" == "--encrypt-file" ]; then
    if [ -z "$2" ]; then
        echo -e "${RED}Error: --encrypt-file requires a filename argument.${NC}"
        exit 1
    fi
    encrypt_new "$2"
    exit $?
fi

while true; do
    show_menu
    read -p "Selection: " choice
    case $choice in
        1) install_all ;;
        2) encrypt_new ;;
        3) use_file ;;
        4) decrypt_all ;;
        5) encrypt_all ;;
        6) add_coworker ;;
        7) remove_coworker ;;
        8) rotate_key ;;
        9) exit 0 ;;
    esac
done