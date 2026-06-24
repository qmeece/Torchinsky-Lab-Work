import config
import SHG_Test
import zaber

def main():
    zaber_instance = zaber.Zaber()
    zaber_instance.start_Zaber()

    SHG_instance = SHG_Test.PulseData()
    SHG_instance.update()

    zaber_instance.close()

if __name__ == "__main__":
    main()
