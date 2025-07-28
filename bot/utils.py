def format_number(value):
    try:
        # Удаляем возможные пробелы и заменяем запятую на точку
        str_value = str(value).strip().replace(" ", "").replace(",", ".")

        # Определяем тип: float или int
        if "." in str_value:
            number = float(str_value)
            int_part, frac_part = str(number).split(".")
            formatted_int = f"{int(int_part):,}".replace(",", " ")
            return f"{formatted_int},{frac_part}"
        else:
            number = int(str_value)
            return f"{number:,}".replace(",", " ")
    except (ValueError, TypeError):
        return "Неверный формат числа"