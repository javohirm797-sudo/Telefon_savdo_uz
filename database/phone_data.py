# Telefon brendlari va modellari bazasi

PHONE_BRANDS = [
    "Apple",
    "Samsung",
    "Xiaomi",
    "Honor",
    "Huawei",
    "Realme",
    "Vivo",
    "Infinix",
    "Tecno",
    "Google Pixel",
    "Boshqa brend"
]

PHONE_MODELS = {
    "Apple": [
        "iPhone 16 Pro Max", "iPhone 16 Pro", "iPhone 16 Plus", "iPhone 16",
        "iPhone 15 Pro Max", "iPhone 15 Pro", "iPhone 15 Plus", "iPhone 15",
        "iPhone 14 Pro Max", "iPhone 14 Pro", "iPhone 14 Plus", "iPhone 14",
        "iPhone 13 Pro Max", "iPhone 13 Pro", "iPhone 13", "iPhone 13 mini",
        "iPhone 12 Pro Max", "iPhone 12 Pro", "iPhone 12", "iPhone 12 mini",
        "iPhone 11 Pro Max", "iPhone 11 Pro", "iPhone 11",
        "iPhone XS Max", "iPhone XS", "iPhone XR", "iPhone X",
        "iPhone SE (2022)", "iPhone SE (2020)", "iPhone 8 Plus", "iPhone 8",
        "Boshqa iPhone modeli"
    ],
    "Samsung": [
        "Galaxy S24 Ultra", "Galaxy S24+", "Galaxy S24",
        "Galaxy S23 Ultra", "Galaxy S23+", "Galaxy S23", "Galaxy S23 FE",
        "Galaxy S22 Ultra", "Galaxy S22+", "Galaxy S22",
        "Galaxy S21 Ultra", "Galaxy S21+", "Galaxy S21", "Galaxy S21 FE",
        "Galaxy S20 Ultra", "Galaxy S20+", "Galaxy S20 FE",
        "Galaxy Z Fold 6", "Galaxy Z Fold 5", "Galaxy Z Fold 4",
        "Galaxy Z Flip 6", "Galaxy Z Flip 5", "Galaxy Z Flip 4",
        "Galaxy Note 20 Ultra", "Galaxy Note 10+",
        "Galaxy A55 5G", "Galaxy A54 5G", "Galaxy A53 5G",
        "Galaxy A35 5G", "Galaxy A34 5G", "Galaxy A25 5G",
        "Galaxy A15", "Galaxy A14", "Galaxy A05s", "Galaxy A05",
        "Galaxy M54", "Galaxy M34",
        "Boshqa Samsung modeli"
    ],
    "Xiaomi": [
        "Xiaomi 14 Ultra", "Xiaomi 14 Pro", "Xiaomi 14",
        "Xiaomi 13 Ultra", "Xiaomi 13 Pro", "Xiaomi 13", "Xiaomi 13T Pro", "Xiaomi 13T",
        "Xiaomi 12 Pro", "Xiaomi 12", "Xiaomi 12T",
        "Redmi Note 13 Pro+ 5G", "Redmi Note 13 Pro 5G", "Redmi Note 13 Pro 4G", "Redmi Note 13",
        "Redmi Note 12 Pro+ 5G", "Redmi Note 12 Pro", "Redmi Note 12S", "Redmi Note 12",
        "Redmi Note 11 Pro", "Redmi Note 11", "Redmi Note 10 Pro",
        "Redmi 13", "Redmi 13C", "Redmi 12", "Redmi 10C", "Redmi 9A",
        "POCO F6 Pro", "POCO F6", "POCO X6 Pro", "POCO X6", "POCO M6 Pro", "POCO X5 Pro", "POCO F5",
        "Boshqa Xiaomi modeli"
    ],
    "Honor": [
        "Honor Magic 6 Pro", "Honor Magic 5 Pro",
        "Honor 200 Pro", "Honor 200", "Honor 200 Lite",
        "Honor 90 Pro", "Honor 90", "Honor 90 Lite",
        "Honor 70", "Honor 50",
        "Honor X9b", "Honor X9a", "Honor X8b", "Honor X8a", "Honor X7b", "Honor X6a",
        "Boshqa Honor modeli"
    ],
    "Huawei": [
        "Huawei Pura 70 Ultra", "Huawei Pura 70 Pro", "Huawei Pura 70",
        "Huawei Mate 60 Pro", "Huawei Mate 50 Pro",
        "Huawei P60 Pro", "Huawei P50 Pro",
        "Huawei Nova 12 Pro", "Huawei Nova 12s", "Huawei Nova 11", "Huawei Nova 10 Pro",
        "Huawei Nova Y91", "Huawei Nova Y90", "Huawei Nova Y70",
        "Boshqa Huawei modeli"
    ],
    "Realme": [
        "Realme GT 6", "Realme GT 5 Pro", "Realme GT Neo 5",
        "Realme 12 Pro+ 5G", "Realme 12 Pro", "Realme 12+", "Realme 12",
        "Realme 11 Pro+ 5G", "Realme 11 Pro", "Realme 11",
        "Realme 10 Pro+", "Realme 10",
        "Realme C67", "Realme C55", "Realme C53", "Realme C51", "Realme Note 50",
        "Boshqa Realme modeli"
    ],
    "Vivo": [
        "Vivo X100 Pro", "Vivo X100", "Vivo X90 Pro",
        "Vivo V30 Pro", "Vivo V30", "Vivo V30e", "Vivo V29 Pro", "Vivo V29", "Vivo V27",
        "Vivo Y200", "Vivo Y100", "Vivo Y36", "Vivo Y27", "Vivo Y17s", "Vivo Y03",
        "iQOO 12", "iQOO Neo 9", "iQOO Z9",
        "Boshqa Vivo modeli"
    ],
    "Infinix": [
        "Infinix GT 20 Pro", "Infinix GT 10 Pro",
        "Infinix Note 40 Pro+ 5G", "Infinix Note 40 Pro", "Infinix Note 40",
        "Infinix Note 30 Pro", "Infinix Note 30",
        "Infinix Zero 30 5G", "Infinix Zero Ultra",
        "Infinix Hot 40 Pro", "Infinix Hot 40", "Infinix Hot 30",
        "Infinix Smart 8", "Infinix Smart 7",
        "Boshqa Infinix modeli"
    ],
    "Tecno": [
        "Tecno Phantom X2 Pro", "Tecno Phantom V Fold",
        "Tecno Camon 30 Premier", "Tecno Camon 30 Pro", "Tecno Camon 30",
        "Tecno Camon 20 Pro", "Tecno Camon 20",
        "Tecno Pova 6 Pro", "Tecno Pova 5 Pro", "Tecno Pova 4",
        "Tecno Spark 20 Pro+", "Tecno Spark 20 Pro", "Tecno Spark 20", "Tecno Spark 10 Pro",
        "Tecno Pop 8",
        "Boshqa Tecno modeli"
    ],
    "Google Pixel": [
        "Pixel 9 Pro XL", "Pixel 9 Pro", "Pixel 9",
        "Pixel 8 Pro", "Pixel 8", "Pixel 8a",
        "Pixel 7 Pro", "Pixel 7", "Pixel 7a",
        "Pixel 6 Pro", "Pixel 6", "Pixel 6a",
        "Boshqa Pixel modeli"
    ],
    "Boshqa brend": [
        "O'zingiz model nomini yozing"
    ]
}

PHONE_MEMORY_OPTIONS = [
    "32 GB",
    "64 GB",
    "128 GB",
    "256 GB",
    "512 GB",
    "1 TB"
]

PHONE_CONDITIONS = [
    "Yangi (Ochilmagan / Plombali)",
    "Ideal (Chiziqsiz / Usta ko'rmagan)",
    "Yaxshi (Yengil ishlatilgan)",
    "O'rtacha (Mayda chiziqlari bor)",
    "Ehtiyot qism / Aybi bor"
]

UZBEKISTAN_REGIONS = [
    "Toshkent shahri",
    "Toshkent viloyati",
    "Samarqand",
    "Farg'ona",
    "Andijon",
    "Namangan",
    "Buxoro",
    "Qashqadaryo",
    "Surxondaryo",
    "Xorazm",
    "Navoiy",
    "Jizzax",
    "Sirdaryo",
    "Qoraqalpog'iston"
]
