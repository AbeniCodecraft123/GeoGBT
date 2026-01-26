import math

def geo_calc():
    print("Welcome to Geo Calculator!")
    print("Available calculations:")
    print("1. Water Saturation")
    print("2. Bulk Density")
    print("3. Effective Porosity")
    print("4. Hydrocarbon Saturation")
    print("5. Seismic Velocity")
    print("6. Gravity Anomaly")
    print("7. Magnetic Anomaly")
    print("8. Telluric Resistivity")
    print("9. Rock Mass Rating")
    print("10. Overburden Pressure")
    print("11. Porosity Estimation")
    print("12. Saturation Index")

    choice = input("Enter calculation type: ").strip().lower()

    try:
        if choice == "water saturation" or choice == "1":
            Rt = float(input("Enter resistivity (ohm·m): "))
            phi = float(input("Enter porosity (%): ")) / 100
            Rw = float(input("Enter water resistivity Rw (default 1): ") or 1)
            Sw = ((Rw)/(phi**2 * Rt))**0.5 * 100
            Sw = max(0, min(Sw, 100))
            print(f"Water Saturation: {Sw:.2f}%")

        elif choice == "bulk density" or choice == "2":
            matrix_density = float(input("Enter matrix density (g/cc): "))
            fluid_density = float(input("Enter fluid density (g/cc): "))
            phi = float(input("Enter porosity (%): ")) / 100
            bulk = phi*fluid_density + (1-phi)*matrix_density
            print(f"Bulk Density: {bulk:.2f} g/cc")

        elif choice == "effective porosity" or choice == "3":
            total_phi = float(input("Enter total porosity (%): ")) / 100
            Swc = float(input("Enter irreducible water saturation (%): ")) / 100
            eff_phi = total_phi*(1-Swc)
            print(f"Effective Porosity: {eff_phi*100:.2f}%")

        elif choice == "hydrocarbon saturation" or choice == "4":
            Sw = float(input("Enter water saturation (%): ")) / 100
            Shc = (1-Sw)*100
            print(f"Hydrocarbon Saturation: {Shc:.2f}%")

        elif choice == "seismic velocity" or choice == "5":
            distance = float(input("Enter distance (m): "))
            time = float(input("Enter time (s): "))
            velocity = distance / time
            print(f"Seismic Velocity: {velocity:.2f} m/s")

        elif choice == "gravity anomaly" or choice == "6":
            delta_m = float(input("Enter mass difference (kg): "))
            d = float(input("Enter distance (m): "))
            g = 6.67430e-11
            anomaly = g * delta_m / d**2
            print(f"Gravity Anomaly: {anomaly:.6e} m/s²")

        elif choice == "magnetic anomaly" or choice == "7":
            m = float(input("Enter magnetic moment (A·m²): "))
            d = float(input("Enter distance (m): "))
            mu0 = 4*math.pi*1e-7
            B = mu0 * m / (4*math.pi*d**3)
            print(f"Magnetic Anomaly: {B:.6e} T")

        elif choice == "telluric resistivity" or choice == "8":
            V = float(input("Enter voltage (V): "))
            I = float(input("Enter current (A): "))
            A = float(input("Enter area (m²): "))
            resistivity = V * A / I
            print(f"Telluric Resistivity: {resistivity:.2f} ohm·m")

        elif choice == "rock mass rating" or choice == "9":
            UCS = float(input("Enter uniaxial compressive strength: "))
            RQD = float(input("Enter RQD: "))
            JS = float(input("Enter joint spacing: "))
            RMR = UCS + RQD + JS
            print(f"Rock Mass Rating (RMR): {RMR:.2f}")

        elif choice == "overburden pressure" or choice == "10":
            depth = float(input("Enter depth (m): "))
            density = float(input("Enter density (kg/m³): "))
            g = 9.81
            pressure = density * g * depth
            print(f"Overburden Pressure: {pressure:.2f} Pa")

        elif choice == "porosity estimation" or choice == "11":
            pore = float(input("Enter pore volume (m³): "))
            bulk = float(input("Enter bulk volume (m³): "))
            phi = (pore / bulk) * 100
            print(f"Estimated Porosity: {phi:.2f}%")

        elif choice == "saturation index" or choice == "12":
            actual = float(input("Enter actual concentration: "))
            max_conc = float(input("Enter max concentration: "))
            SI = actual / max_conc
            print(f"Saturation Index: {SI:.2f}")

        else:
            print("Unknown calculation type.")

    except Exception as e:
        print("Calculation failed:", e)


if __name__ == "__main__":
    geo_calc()
