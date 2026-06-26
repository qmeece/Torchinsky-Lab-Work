import experiment
import cryo

file = ("file info")

def main():
    for i in range(10):
        experiment.run(
            file = file,
            Polarization = "H",
            averages = 100
        )

        cryo.set_relative(20 - i)

if __name__ == "__main__":
    main()