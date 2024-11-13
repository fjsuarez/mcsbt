import password_manager as pm

menu = {
    1: ["Create password", pm.create_new_password],
    2: ["Export passwords", pm.export_passwords],
    0: ["Exit"]
}

while True:
    for key, value in menu.items():
        print(f"{key}. {value[0]}")
    option = int(input("Choose an option: "))
    if option == 0:
        break
    menu[option][1]()
