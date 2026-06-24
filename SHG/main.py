import config
import SHG_Test
import zaber
import time

def main():
    zaber_instance = zaber.Zaber()
    zaber_instance.start_Zaber(39000)
    try:
        SHG_instance = SHG_Test.PulseData()
        SHG_instance.update()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        zaber_instance.close()

if __name__ == "__main__":
    main()
