#!/usr/bin/python

import argparse
from string import Template


SCALAR_TEMPLATE = """
record(calc, "$$(P):TEST_$num") {
    field(VAL,"0")
    field(INPA,"$$(P):TEST_$num")
    field(CALC,"A+1")
    field(SCAN,".1 second")
}

"""

WAVEFORM_TEMPLATE = """
record(waveform, "$$(P):TEST_WVF-DOUBLE${size}_${num}")
{
    field(SCAN, "Passive")
    field(NELM, "${size}")
    field(FTVL, "DOUBLE")
}

"""


def generate_scalars(numof=100):
    template = Template(SCALAR_TEMPLATE)
    output_records = []

    for i in range(numof):
        output_records.append(template.substitute(num=i))

    print(
        f"Generated  {numof} scalar records. Name format: $(P):TEST_[0-{numof}]")
    return output_records


def generate_waveforms(numof=10, size=1024):
    template = Template(WAVEFORM_TEMPLATE)
    output_records = []

    for i in range(numof):
        output_records.append(template.substitute(num=i, size=size))

    print("Generated  {} waveform records of size {} Name format: $(P):TEST_WVF-DOUBLE{}_[0-{}]"
          .format(numof, size, size, numof))
    return output_records


def scalar(numof):
    g_output_records.extend(generate_scalars(numof))
    global g_total_payload_size
    g_total_payload_size = g_total_payload_size + numof * 8


def waveform(numof, size):
    g_output_records.extend(generate_waveforms(numof, size))
    global g_total_payload_size
    g_total_payload_size = g_total_payload_size + numof * size * 8


def safe_eval(input):
    """
    A stupid safe-ish eval
    """
    eval(input, {"__builtins__": None, "scalar": scalar, "waveform": waveform}, {})


def create_db(input, filename=None):
    for c in input.split(";"):
        safe_eval(c)

    if len(g_output_records):
        print("Generated {} records with total payload size {:}kB".format(
            len(g_output_records), g_total_payload_size / 1024))

    if filename:
        print(f"Writing generated records to file {filename}")
        f = open(filename, "w+")
        f.write("".join(g_output_records))
        f.close()


#TODO:
g_output_records = []
g_total_payload_size = 0





if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate a variable number of scalar records")
    parser.add_argument(
        "input", type=str, help='generator strings (e.g. "scalar(10);waveform(10,1024)"')
    parser.add_argument("-filename", "-f", type=str, help="output filename")
    args = parser.parse_args()
    create_db(args.input, args.filename)



