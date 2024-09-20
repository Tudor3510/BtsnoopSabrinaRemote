import os
import json
import btsnoop.btsnoop.btsnoop as bts
import btsnoop.bt.hci_uart as hci_uart
import btsnoop.bt.hci_cmd as hci_cmd
import btsnoop.bt.hci_evt as hci_evt
import btsnoop.bt.hci_acl as hci_acl
import btsnoop.bt.hci_sco as hci_sco
import btsnoop.bt.l2cap as l2cap
import btsnoop.bt.att as att
import btsnoop.bt.smp as smp

# In the input file, the desired record numbers should be indexed from 1, like in WireShark

# Write down the accepted handles
DESIRED_HANDLE = "53"
INDEXING_HANDLE = "55"
INDEXING_PREFIX = "77"
ACCEPTED_BUTTONS = ["volume", "power", "input"]
ARRAY_INFORMATION_FOR_BUTTON = "volume"


def read_le_att_value(records, desired_record_no, handles, indexing_handle, indexing_prefix):
    sel_record = records[desired_record_no]
    hci_pkt_type, hci_pkt_data = hci_uart.parse(sel_record[4])
    hci_data = hci_acl.parse(hci_pkt_data)
    l2cap_length, l2cap_cid, l2cap_data = l2cap.parse(hci_data[2], hci_data[4])
    att_opcode, att_data = att.parse(l2cap_data)

    if att_opcode != 18 and att_opcode != 22:
        raise Exception("Not a write request or prepare write request!")     # or prepare write request

    if att_data.hex()[:2] not in handles:
        raise Exception("Not an accepted handle!")
    
    if att_data.hex()[:2] == indexing_handle and att_data.hex()[4:6] == indexing_prefix:
        if att_data.hex()[7] == "0":
            return True, att_data.hex()[8:]
        return True, att_data.hex()[7:]

    if att_opcode == 22:
        return False, att_data.hex()[8:]
    return False, att_data.hex()[4:]





records = bts.parse("btsnoop_hci.log")

input = open("recordsNoIn.txt", "r")
output_json_file_name = input.readline().strip()
button = input.readline().strip()

if button not in ACCEPTED_BUTTONS:
    raise Exception("Not an accepted button name!")


json_data = {}
try:
    output = open(output_json_file_name, "r")
    json_data = json.load(output)
    output.close()
except FileNotFoundError:
    print(f"The file '{output_json_file_name}' was not found.")


already_reset = {}
for k in json_data.keys():
    already_reset[k] = False


index = ""
for line in input:
    desired_records_no = line.strip().split()
    if len(desired_records_no) == 0:
        continue

    final_hex = ""
    for desired_record_no in desired_records_no:
        is_index, value_hex = read_le_att_value(records, int(desired_record_no) - 1, [DESIRED_HANDLE] + [INDEXING_HANDLE], INDEXING_HANDLE, INDEXING_PREFIX)
        if is_index:
            index = value_hex
            final_hex = "index_packet"
            if index not in json_data:
                json_data[index] = {}

            if button == ARRAY_INFORMATION_FOR_BUTTON and ((index in already_reset and not already_reset[index]) or index not in already_reset):
                already_reset[index] = True
                json_data[index][button] = []
            break

        if index == "":
            raise Exception("Not starting with a packet for indexing")
        
        final_hex += value_hex

    if final_hex == "":
        raise Exception("Could not get a valid hex string for the packet")
    
    if final_hex == "index_packet":         # the packet for indexing should not
        continue                            # have another packet on its line
    
    if button == ARRAY_INFORMATION_FOR_BUTTON:
        json_data[index][button].append(final_hex)
    else:
        json_data[index][button] = final_hex


output = open(output_json_file_name, "w")
json.dump(json_data, output, indent=4)

input.close()
output.close()

