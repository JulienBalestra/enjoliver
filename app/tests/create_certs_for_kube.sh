#!/usr/bin/env bash

set -o pipefail

CERTS_PATH="${HOME}/.kube/certs"



usage() {
    echo "Script will connect to each server defined in file and generate certs. All files will be saved in ~/.kube/certs directory"
    echo "You must have ssh certs to login to remote cp"
    echo "Usage: "
    echo "To generate certs for all server from file: $0 -f serevr-list.json -c common-name"
    echo "To generate certs only for one given server: $0 -m -c common-name -s server-ip -u server-user-name -n server-name"
    echo "Parameters explanation:"
    echo "  -f - json file "
    echo "  -m - manual mode"
    echo "  -c - common name (username for your certificate)"
    echo "  -s - server ip "
    echo "  -u - server ssh username"
    echo "  -n - server name (used to define config in k8s)"
    exit 0
}


req_check() {
    which jq > /dev/null
    if [ $? -ne 0 ]
    then
        echo "Need jq to generate certs, install it and rerun script"
        exit 2
    fi
}

check_and_create_certs_directory() {
    if [ ! -d "${HOME}/.kube/certs" ]
    then
        echo "Kube certs directory doesn't exists, creating."
        mkdir -p ~/.kube/certs
    fi
}

_generate_cert_name_and_path() {
    cert_name=$1
    cp_name=$2
    user_name=$3
    echo ${CERTS_PATH}/${cp_name}-${user_name}.${cert_name}
}

add_k8s_config() {
    common_name=$1
    cp_name=$2
    cp_ip=$3

    cert=$(_generate_cert_name_and_path "cert" ${cp_name} ${common_name})
    isca=$(_generate_cert_name_and_path "isca" ${cp_name} ${common_name})
    priv=$(_generate_cert_name_and_path "priv" ${cp_name} ${common_name})

    kubectl config set-cluster ${cp_name} \
        --server=https://${cp_ip}:6443 \
        --certificate-authority=${isca} > \dev\null

    kubectl config set-credentials ${common_name}@${cp_name} \
        --client-key=${priv} \
        --client-certificate=${cert} > \dev\null

    kubectl config set-context ${cp_name} \
        --cluster=${cp_name} \
        --user=${common_name}@${cp_name} > \dev\null

}

generate_cert_for_server() {
    common_name=$1
    cp_name=$2
    cp_username=$3
    cp_ip=$4

    SSH_OUTPUT=$(ssh ${cp_username}@${cp_ip} "bash -s -l" < create_certs_for_kube_remote.sh ${common_name}  2>&1)
#    SSH_OUTPUT=$(ssh -i testing.rsa ${cp_username}@${cp_ip} "bash -s -l" < create_certs_for_kube_remote.sh ${common_name})

    if [ $? -ne 0 ]
    then
        echo ${SSH_OUTPUT} >> $0.error.log
        echo 1
    else
        echo ${SSH_OUTPUT} | jq .private_key -r > $(_generate_cert_name_and_path "priv" ${cp_name} ${common_name})
        echo ${SSH_OUTPUT} | jq .issuing_ca -r > $(_generate_cert_name_and_path "isca" ${cp_name} ${common_name})
        echo ${SSH_OUTPUT} | jq .certificate -r > $(_generate_cert_name_and_path "cert" ${cp_name} ${common_name})

        echo 0
    fi

}

generate_cert() {
    common_name=$1
    cp_name=$2
    cp_username=$3
    cp_ip=$4

    echo "Generating certificate for ${common_name} at ${cp_name} -> ${cp_username}@${cp_ip}"
    output=$(generate_cert_for_server ${common_name} ${cp_name} ${cp_username} ${cp_ip})

    if [ ${output} -eq 0 ]; then
        echo "Certificates generated."
        echo "Adding configuration to kubernates."
        add_k8s_config ${common_name} ${cp_name} ${cp_ip}
        echo "Configuration completed."
    else
        echo "Generating certificates failed. Check $0.error.log for more info."
    fi
    echo "----------------"
}


generate_manual() {
   for i in "$@"
    do
        case $i in
            -u=*|--user-name=*)
            cp_username="${i#*=}"
            shift
            ;;
            -s=*|--server-ip=*)
            cp_ip="${i#*=}"
            shift
            ;;
            -n=*|--server-name=*)
            cp_name="${i#*=}"
            shift
            ;;
            -c=*|--common-name*)
            common_name="${i#*=}"
            shift
            ;;
            --manual|-m)
            shift
            ;;
            *)
            echo "Parameter '"$i"' is unknown for manual mode "
            exit 2
            ;;
        esac
    done

    if [ -z ${cp_username} ] || [ -z ${cp_name} ] || [ -z ${cp_ip} ] || [ -z ${common_name} ]; then
        echo "Invalid arguments."
        usage
        exit 3
    fi

    generate_cert ${common_name} ${cp_name} ${cp_username} ${cp_ip}

}

generate_from_file() {
   for i in "$@"
    do
        case $i in
            -c*|--common-name*)
            common_name="${i#*=}"
            shift
            ;;
            -f*|--file*)
            file_name="${i#*=}"
            shift
            ;;
            *)
            echo "Parameter '"$i"' is unknown for file mode "
            exit 2
            ;;
        esac
    done

    if [ -z ${file_name} ] || [ -z ${common_name} ]; then
        echo "Invalid arguments."
        usage
        exit 3
    fi

    while IFS= read -r cp_name &&
              IFS= read -r cp_ip &&
              IFS= read -r cp_username
    do
        generate_cert ${common_name} ${cp_name} ${cp_username} ${cp_ip}
    done < <(jq -r '.[] | (.name, .ip, .username)' ${file_name})

}

main() {
    req_check
    check_and_create_certs_directory

    case "$@" in
        -m*|--manual*)
            generate_manual $@
        ;;
        -f=*|--file=*)
            generate_from_file $@
        ;;
        -h|--help)
            usage
        ;;
    esac

    echo "Run kubectl config get-contexts to see new configuration."
}

main $@
