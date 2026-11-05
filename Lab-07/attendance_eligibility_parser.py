
def normalize_srn(srn):
    if not isinstance(srn, str):
        return ""
    return srn.strip().replace(' ', '').upper()


def attendance_from_ratio(text):
    try:
        attended, held = text.split('/')
        attended = int(attended)
        held = int(held)

        if attended < 0 or held <= 0 or attended > held:
            return 0

        return attended * 100 // held
    except (ValueError, AttributeError, TypeError):
        return 0


def attendance_from_register(marks):
    if not isinstance(marks, str):
        return 0

    marks = marks.strip().upper()

    if not marks or any(ch not in 'PA' for ch in marks):
        return 0

    return marks.count('P') * 100 // len(marks)


def main():
    print("==== Running normalize_srn ====")
    value = input("Enter an SRN (e.g. pes1ug23cs001): ")
    print("Normalized SRN:", normalize_srn(value))

    print("\n==== Running attendance_from_ratio ====")
    value = input("Enter classes attended and held as ATTENDED/HELD (e.g. 30/40): ")
    print("Attendance percent:", attendance_from_ratio(value))

    print("\n==== Running attendance_from_register ====")
    value = input("Enter the register as P/A marks (e.g. PPAPP): ")
    print("Attendance percent:", attendance_from_register(value))


if __name__ == "__main__":
    main()
