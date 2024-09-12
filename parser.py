import os
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
    
    print (att_data.hex()[4:6])
    if att_data.hex()[:2] == indexing_handle and att_data.hex()[4:6] == indexing_prefix:
        if att_data.hex()[7] == "0":
            return True, att_data.hex()[8:]
        return True, att_data.hex()[7:]

    if att_opcode == 22:
        return False, att_data.hex()[8:]
    return False, att_data.hex()[4:]

records = bts.parse("btsnoop_hci.log")

input = open("recordsNoIn.txt", "r")
output = open("packetsOutput.txt", "w")

for line in input:
    desired_records_no = line.strip().split()

    for desired_record_no in desired_records_no:
        is_index, value_hex = read_le_att_value(records, int(desired_record_no) - 1, [DESIRED_HANDLE] + [INDEXING_HANDLE], INDEXING_HANDLE, "99")
        output.write(value_hex)
    output.write("\n")

input.close()
output.close()

