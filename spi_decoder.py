#! python
import pandas as pd
from sys import argv

def convert_csv_to_dataframe(filename):
  """
  Converts a CSV file into a pandas dataframe.

  Args:
      filename: The path to the CSV file.

  Returns:
      A pandas dataframe containing the data from the CSV file.
  """
  try:
    df = pd.read_csv(filename, sep=";", decimal=",")
    return df
  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return None

def convert_analog_to_digital(data, threshold_low=0.8, threshold_high=2.0):
  """
  Converts an analog signal to a digital signal with hysteresis.

  Args:
      data: A list of analog values.
      threshold_low: The lower threshold for the digital signal (low to high).
      threshold_high: The upper threshold for the digital signal (high to low).

  Returns:
      A list of digital values (0 or 1).
  """
  data_filt = []
  previous_data = None
  first = True
  for value in data:
    if first:
      if value >= threshold_high:
          previous_data = 1
      elif value <= threshold_low:
          previous_data = 0
      data_filt.append(previous_data)
      first = False
      continue

    if value >= threshold_high and 0 == previous_data:
      previous_data = 1
    elif value <= threshold_low and 1 == previous_data:
      previous_data = 0
    # else, keep previous_data

    data_filt.append(previous_data)

  return data_filt

def latch_data_on_sclk_to_bitstream(sclk_digital, data_digital, rising_edge=True):
  """
  Latches data on the rising edge of the SCLK signal.

  Args:
      sclk_digital: The name of the column containing the SCLK data digitally cleaned.
      data_digital: The name of the column containing the MOSI or MISO data digitally cleaned.
      rising_edge: If True, latches data on rising edge. Latches on falling edge otherwise

  Returns:
      A list of latched data values.
  """

  if len(sclk_digital) != len(data_digital):
    raise Exception("Lengths must match!")

  bit_stream = []

  for i in range(1, len(sclk_digital)):
    if rising_edge:
      if 1 == sclk_digital[i] and 0 == sclk_digital[i-1]:
        bit_stream.append(data_digital[i])
    else:
      if 0 == sclk_digital[i] and 1 == sclk_digital[i-1]:
        bit_stream.append(data_digital[i])

  return bit_stream

def decode_bitstream(bitstream, group_by=8, MSB_first=True, hexadecimal=True):
  total_length = len(bitstream)

  if total_length % group_by != 0:
    raise Exception(f"Cannot group {group_by} bits in a {total_length} long stream without leaving any bit out!")

  groups_count = int(total_length / group_by)

  grouped_stream = []

  for i in range(groups_count):
    group = bitstream[i*group_by:group_by+i*group_by]

    # If MSB first, invert group to start ORing the bits into the number from the LSB
    ordered_group = group[::-1] if MSB_first else group

    number = 0
    for j, bit in enumerate(ordered_group):
      number |= (bit << j)

    if hexadecimal:
      grouped_stream.append(hex(number))
    else:
      grouped_stream.append(number)

  return grouped_stream

def main():
  """
  The main function that reads the CSV, converts data, and latches on SCLK.
  """

  if len(argv) < 2:
    raise AttributeError("Filename must be passed as argument")

  for filename in argv[1:]:
    df = convert_csv_to_dataframe(filename)
    if df is not None:
      sclk = convert_analog_to_digital(df.iloc[:, 1])

      signal = convert_analog_to_digital(df.iloc[:, 2])  # Adjust thresholds if needed
      # latched_data = latch_data_on_sclk(df, "SCLK", "MOSI_MISO")  # Replace "MOSI" with "MISO" if using MISO data

      bit_stream = latch_data_on_sclk_to_bitstream(sclk, signal)

      decoded = decode_bitstream(bit_stream)
      # Process or display the latched data as needed
      print(f"Decoded data from {filename}:", end="\n  -> ")
      print(decoded)

if __name__ == "__main__":
  main()

