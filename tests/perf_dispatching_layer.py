import argparse
import logging
import socket
from time import time

from bsread import SUB, Source


channels_to_save = [
    "SAROP21-CVME-PBPS2:Lnk9Ch7-BG-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch7-BG-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch7-BG-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch7-BG-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch7-BG-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch7-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch7-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch7-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch7-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch7-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-BG-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-BG-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-BG-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-BG-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-BG-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch12-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-BG-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-BG-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-BG-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-BG-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-BG-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch13-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-BG-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-BG-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-BG-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-BG-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-BG-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch14-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-BG-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-BG-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-BG-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-BG-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-BG-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-DATA",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-DATA-CALIBRATED",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-DATA-SUM",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-DRS_TC",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-PULSEID-valid",
    "SAROP21-CVME-PBPS2:Lnk9Ch15-WD_FREQ",
    "SARFE10-CVME-PHO6211:Lnk9Ch12-BG-DATA",
    "SARFE10-CVME-PHO6211:Lnk9Ch12-BG-DATA-CALIBRATED",
    "SARFE10-CVME-PHO6211:Lnk9Ch12-BG-DRS_TC",
    "SARFE10-CVME-PHO6211:Lnk9Ch12-DATA",
    "SARFE10-CVME-PHO6211:Lnk9Ch12-DATA-CALIBRATED",
    "SARFE10-CVME-PHO6211:Lnk9Ch12-DATA-SUM",
    "SARFE10-CVME-PHO6211:Lnk9Ch12-DRS_TC",
    "SARFE10-CVME-PHO6211:Lnk9Ch13-BG-DATA",
    "SARFE10-CVME-PHO6211:Lnk9Ch13-BG-DATA-CALIBRATED",
    "SARFE10-CVME-PHO6211:Lnk9Ch13-BG-DRS_TC",
    "SARFE10-CVME-PHO6211:Lnk9Ch13-DATA",
    "SARFE10-CVME-PHO6211:Lnk9Ch13-DATA-CALIBRATED",
    "SARFE10-CVME-PHO6211:Lnk9Ch13-DATA-SUM",
    "SARFE10-CVME-PHO6211:Lnk9Ch13-DRS_TC",
    "SARFE10-CVME-PHO6211:Lnk9Ch14-BG-DATA",
    "SARFE10-CVME-PHO6211:Lnk9Ch14-BG-DATA-CALIBRATED",
    "SARFE10-CVME-PHO6211:Lnk9Ch14-BG-DRS_TC",
    "SARFE10-CVME-PHO6211:Lnk9Ch14-DATA",
    "SARFE10-CVME-PHO6211:Lnk9Ch14-DATA-CALIBRATED",
    "SARFE10-CVME-PHO6211:Lnk9Ch14-DATA-SUM",
    "SARFE10-CVME-PHO6211:Lnk9Ch14-DRS_TC",
    "SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DATA",
    "SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DATA-CALIBRATED",
    "SARFE10-CVME-PHO6211:Lnk9Ch15-BG-DRS_TC",
    "SARFE10-CVME-PHO6211:Lnk9Ch15-DATA",
    "SARFE10-CVME-PHO6211:Lnk9Ch15-DATA-CALIBRATED",
    "SARFE10-CVME-PHO6211:Lnk9Ch15-DATA-SUM",
    "SARFE10-CVME-PHO6211:Lnk9Ch15-DRS_TC",
    "SARFE10-PBPG050:HAMP-INTENSITY",
    "SARFE10-PBPG050:HAMP-INTENSITY-AVG",
    "SARFE10-PBPG050:HAMP-INTENSITY-CAL",
    "SARFE10-PBPG050:HAMP-XPOS",
    "SARFE10-PBPG050:HAMP-YPOS"]


def run_tests(n_tests, n_messages, log_level="ERROR"):

    dispatching_layer_request_times = []
    first_message_request_times = []
    other_messages_request_times = []

    logging.basicConfig(level=log_level)

    for index_test in range(n_tests):
        print(f"Starting test {index_test+1}/{n_tests}")

        start_time = time()
        with Source(channels=channels_to_save, mode=SUB) as input_stream:
            end_time = time()
            dispatching_layer_request_times.append(end_time - start_time)

            print("Connected to dispatching layer.")

            start_time = time()
            input_stream.receive()
            end_time = time()
            first_message_request_times.append(end_time - start_time)

            print("First message received.")

            current_test_receive_times = []

            for index_message in range(n_messages):
                print(f"Received message {index_message+1}/{n_messages}.")
                start_time = time()
                input_stream.receive()
                end_time = time()

                current_test_receive_times.append(end_time - start_time)

            other_messages_request_times.append(current_test_receive_times)

    dispatching_layer_avg_time = sum(dispatching_layer_request_times) / len(dispatching_layer_request_times)

    first_message_avg_time = sum(first_message_request_times) / len(first_message_request_times)

    other_messages_avg_per_test = [sum(x) / len(x) for x in other_messages_request_times]
    other_messages_avg_time = sum(other_messages_avg_per_test) / len(other_messages_avg_per_test)

    hostname = socket.gethostname()
    print(f"Test parameters: hostname: {hostname}; n_tests: {n_tests}; n_messages: {n_messages};")
    print(f"Dispatching layer average time to connect (seconds): {dispatching_layer_avg_time:.3f}")
    print(f"First message average time (seconds): {first_message_avg_time:.3f}")
    print(f"Non-first messages average time (seconds): {other_messages_avg_time:.3f}")
    print(f"Non-first message frequency (Hz): {1 / other_messages_avg_time:.3f}")





if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test dispatching layer performance.")

    parser.add_argument("n_tests", type=int, help="Number of test iterations.")
    parser.add_argument("n_messages", type=int, help="How many messages to receive in each iteration.")
    inputs = parser.parse_args()

    run_tests(inputs.n_tests, inputs.n_messages)



