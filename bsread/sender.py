from .bsread import Generator, Channel


def my_function(pulse_id):
    return float(pulse_id)*10

if __name__ == "__main__":
    generator = Generator()
    generator.add_channel('ABC', my_function)
    generator.add_channel('ABCD', my_function)
    generator.add_channel('ABCDF', my_function)
    generator.generate_stream()