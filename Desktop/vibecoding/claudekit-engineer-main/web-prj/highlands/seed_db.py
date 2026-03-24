"""
Create all tables and seed initial data: categories, products, stores, news, promotions.
Run once: python -m highlands.seed_db
"""
from highlands.database import engine, SessionLocal
from highlands.models import Base, Category, Product, Store, News, Promotion

# ── Categories (must match Product.category values exactly) ─
CATEGORIES = [
    Category(id=1, name="Cà Phê",  emoji="☕"),
    Category(id=2, name="Trà",     emoji="🧋"),
    Category(id=3, name="Đá Xay",  emoji="🥤"),
    Category(id=4, name="Đồ Ăn",  emoji="🥐"),
    Category(id=5, name="Combo",   emoji="🎁"),
]

# ── 30 Products ────────────────────────────────────────────

PRODUCTS = [
    # Coffee (10)
    Product(id=1,  name="Cà Phê Sữa Đá",            category="Cà Phê",  price=39000, emoji="☕", description="Cà phê Arabica hảo hạng pha phin, ngọt ngào với sữa đặc"),
    Product(id=2,  name="Cà Phê Đen Đá",             category="Cà Phê",  price=29000, emoji="☕", description="Robusta Tây Nguyên nguyên chất, đậm vị mạnh mẽ"),
    Product(id=3,  name="Cà Phê Trứng",              category="Cà Phê",  price=45000, emoji="☕", description="Cà phê phủ lớp kem trứng béo mịn đặc trưng Hà Nội"),
    Product(id=4,  name="Cappuccino",                 category="Cà Phê",  price=55000, emoji="☕", description="Espresso Ý kết hợp sữa nóng tạo bọt mịn hoàn hảo"),
    Product(id=5,  name="Latte",                      category="Cà Phê",  price=55000, emoji="☕", description="Espresso nhẹ nhàng với sữa nóng mịn, ít đắng"),
    Product(id=6,  name="Americano",                  category="Cà Phê",  price=49000, emoji="☕", description="Espresso đậm pha loãng với nước nóng, thanh sạch"),
    Product(id=7,  name="Mocha",                      category="Cà Phê",  price=59000, emoji="☕", description="Cà phê sô-cô-la hòa quyện sữa tươi và kem Chantilly"),
    Product(id=8,  name="Cold Brew Đá Muối",          category="Cà Phê",  price=65000, emoji="☕", description="Ngâm lạnh 18 giờ, phủ muối hồng Himalaya"),
    Product(id=9,  name="Espresso Tonic",             category="Cà Phê",  price=59000, emoji="☕", description="Espresso đổ lên nước tonic vị chanh sảng khoái"),
    Product(id=10, name="Cà Phê Dừa",                category="Cà Phê",  price=55000, emoji="☕", description="Cà phê sữa đặc kết hợp nước cốt dừa béo ngậy"),

    # Tea (8)
    Product(id=11, name="Trà Sữa Taro",              category="Trà",     price=45000, emoji="🧋", description="Khoai môn tươi xay nhuyễn, trà ô long thơm ngát"),
    Product(id=12, name="Matcha Latte Đặc Biệt",     category="Trà",     price=49000, emoji="🍵", description="Matcha Nhật hạng A, sữa tươi Đà Lạt tươi mát"),
    Product(id=13, name="Trà Đào Cam Sả",            category="Trà",     price=42000, emoji="🍑", description="Đào tươi, cam ngọt, sả thơm, đá viên mát lạnh"),
    Product(id=14, name="Trà Xanh Latte",            category="Trà",     price=45000, emoji="🍵", description="Trà xanh Thái Nguyên, sữa tươi Đà Lạt béo nhẹ"),
    Product(id=15, name="Trà Ô Long Sữa",            category="Trà",     price=45000, emoji="🧋", description="Trà ô long đậm vị, sữa tươi thơm mượt mà"),
    Product(id=16, name="Trà Dâu Tây",               category="Trà",     price=48000, emoji="🍓", description="Dâu tây tươi xay nhuyễn, trà trắng thanh nhẹ"),
    Product(id=17, name="Trà Hoa Cúc Mật Ong",       category="Trà",     price=39000, emoji="🌼", description="Hoa cúc tươi ngâm với mật ong thiên nhiên"),
    Product(id=18, name="Trà Bạc Hà Chanh Leo",      category="Trà",     price=42000, emoji="🌿", description="Bạc hà tươi, chanh leo mát lạnh, giải nhiệt tuyệt vời"),

    # Freeze (5)
    Product(id=19, name="Freeze Cà Phê",             category="Đá Xay",  price=55000, emoji="🥤", description="Đá xay cà phê Arabica, kem tươi phủ trên mặt"),
    Product(id=20, name="Freeze Matcha",             category="Đá Xay",  price=59000, emoji="🥤", description="Đá xay matcha Nhật, sữa tươi, kem tươi mịn"),
    Product(id=21, name="Freeze Taro",               category="Đá Xay",  price=59000, emoji="🥤", description="Đá xay khoai môn tím, thơm béo ngây ngất"),
    Product(id=22, name="Freeze Dâu Tây",            category="Đá Xay",  price=59000, emoji="🥤", description="Dâu tây tươi xay đá, kem tươi phủ ngọt ngào"),
    Product(id=23, name="Freeze Chocolate",          category="Đá Xay",  price=59000, emoji="🥤", description="Sô-cô-la đậm đà xay đá, kem tươi mịn màng"),

    # Food (5)
    Product(id=24, name="Croissant Bơ Pháp",         category="Đồ Ăn",    price=35000, emoji="🥐", description="Nướng mới mỗi sáng, vỏ giòn tan, thơm bơ nhẹ"),
    Product(id=25, name="Bánh Mì Sandwich Gà",       category="Đồ Ăn",    price=45000, emoji="🥪", description="Gà nướng mật ong, rau tươi, sốt mayonnaise Nhật"),
    Product(id=26, name="Bánh Tiramisu",             category="Đồ Ăn",    price=55000, emoji="🍰", description="Bánh Ý truyền thống, cà phê espresso thấm đều"),
    Product(id=27, name="Bánh Madeleine",            category="Đồ Ăn",    price=29000, emoji="🧁", description="Bánh bông lan Pháp nhỏ xinh, thơm bơ vani"),
    Product(id=28, name="Sandwich Cá Ngừ",           category="Đồ Ăn",    price=45000, emoji="🥙", description="Cá ngừ tươi, dưa leo giòn, sốt kem phô mai"),

    # Combo (2)
    Product(id=29, name="Combo Sáng — Cà Phê & Croissant", category="Combo", price=65000, emoji="🎁", description="1 Cà phê sữa đá + 1 Croissant bơ Pháp, tiết kiệm 9.000đ"),
    Product(id=30, name="Combo Chiều — Trà & Bánh",        category="Combo", price=75000, emoji="🎁", description="1 Trà đào cam sả + 1 Bánh tiramisu, tiết kiệm 22.000đ"),
]


# ── 12 Stores ──────────────────────────────────────────────

STORES = [
    # Hà Nội
    Store(id=1,  name="Highlands Coffee – Vincom Bà Triệu",    address="191 Bà Triệu",               district="Hai Bà Trưng",  city="Hà Nội",   phone="024 3974 0001", hours="06:30 – 22:30"),
    Store(id=2,  name="Highlands Coffee – Lotte Center",       address="54 Liễu Giai",               district="Ba Đình",       city="Hà Nội",   phone="024 3831 0002", hours="07:00 – 22:00"),
    Store(id=3,  name="Highlands Coffee – Tràng Tiền Plaza",   address="24 Hai Bà Trưng",            district="Hoàn Kiếm",     city="Hà Nội",   phone="024 3936 0003", hours="07:00 – 22:30"),
    Store(id=4,  name="Highlands Coffee – Times City",         address="458 Minh Khai",              district="Hai Bà Trưng",  city="Hà Nội",   phone="024 3636 0004", hours="07:00 – 22:00"),
    Store(id=5,  name="Highlands Coffee – Royal City",         address="72A Nguyễn Trãi",            district="Thanh Xuân",    city="Hà Nội",   phone="024 3511 0005", hours="07:00 – 22:00"),

    # TP.HCM
    Store(id=6,  name="Highlands Coffee – Vincom Đồng Khởi",  address="72 Lê Thánh Tôn",            district="Quận 1",        city="TP.HCM",   phone="028 3822 0006", hours="06:30 – 23:00"),
    Store(id=7,  name="Highlands Coffee – Crescent Mall",     address="101 Tôn Dật Tiên",           district="Quận 7",        city="TP.HCM",   phone="028 5413 0007", hours="07:00 – 22:30"),
    Store(id=8,  name="Highlands Coffee – SC VivoCity",       address="1058 Nguyễn Văn Linh",       district="Quận 7",        city="TP.HCM",   phone="028 5416 0008", hours="07:00 – 22:00"),
    Store(id=9,  name="Highlands Coffee – Aeon Mall Bình Tân", address="1 Đường Số 17A",            district="Bình Tân",      city="TP.HCM",   phone="028 3750 0009", hours="08:00 – 22:00"),

    # Đà Nẵng
    Store(id=10, name="Highlands Coffee – Vincom Đà Nẵng",    address="910A Ngô Quyền",             district="Sơn Trà",       city="Đà Nẵng",  phone="0236 374 0010", hours="07:00 – 22:00"),
    Store(id=11, name="Highlands Coffee – Đà Nẵng Center",    address="15 Lý Tự Trọng",             district="Hải Châu",      city="Đà Nẵng",  phone="0236 381 0011", hours="07:00 – 22:30"),
    Store(id=12, name="Highlands Coffee – Sun World Đà Nẵng", address="1 Phan Đình Phùng",          district="Hải Châu",      city="Đà Nẵng",  phone="0236 382 0012", hours="06:30 – 23:00"),
]


# ── 6 Promotions ───────────────────────────────────────────

PROMOTIONS = [
    Promotion(id=1, title="Mua 1 Tặng 1 Cà Phê",           description="Mua 1 ly cà phê bất kỳ tặng ngay 1 ly cùng loại cho bạn bè. Áp dụng từ 14:00 – 17:00 mỗi ngày.", discount="Mua 1 tặng 1", emoji="☕", tag="HOT",  valid_until="31/12/2026"),
    Promotion(id=2, title="Giảm 20% Thứ Hai Hàng Tuần",    description="Giảm 20% toàn bộ menu mỗi thứ Hai. Áp dụng khi thanh toán qua ứng dụng Highlands Coffee.",          discount="20%",         emoji="💸", tag="SALE", valid_until="31/12/2026"),
    Promotion(id=3, title="Combo Sinh Nhật Đặc Biệt",       description="Tặng 1 bánh kem mini và 1 ly đồ uống tùy chọn nhân dịp sinh nhật. Xuất trình CCCD xác nhận.",        discount="Quà tặng",    emoji="🎂", tag="NEW",  valid_until="31/12/2026"),
    Promotion(id=4, title="Thẻ Thành Viên – Tích Điểm x2", description="Thành viên Gold và Platinum được nhân đôi điểm tích lũy cả tháng 4. Đổi điểm lấy đồ uống miễn phí.", discount="Điểm x2",    emoji="⭐", tag="HOT",  valid_until="30/04/2026"),
    Promotion(id=5, title="Giảm 15% Đơn Hàng Online",      description="Đặt hàng qua website hoặc app được giảm ngay 15% cho đơn hàng đầu tiên mỗi tháng.",                   discount="15%",         emoji="📱", tag="NEW",  valid_until="30/06/2026"),
    Promotion(id=6, title="Happy Hour 15:00 – 17:00",       description="Tất cả đồ uống freeze và trà sữa giảm 25% trong khung giờ vàng 15:00 – 17:00 mỗi ngày thường.",       discount="25%",         emoji="⏰", tag="SALE", valid_until="31/03/2026"),
]


# ── 6 News Articles ────────────────────────────────────────

NEWS = [
    News(id=1, title="Highlands Coffee Ra Mắt Bộ Sưu Tập Cà Phê Đặc Sản Việt 2026",
         excerpt="6 loại cà phê đặc sản từ các vùng trồng nổi tiếng của Việt Nam, mang hương vị độc đáo đặc trưng từng địa phương.",
         content="Highlands Coffee tự hào giới thiệu bộ sưu tập cà phê đặc sản Việt Nam 2026 với 6 dòng sản phẩm được tuyển chọn kỹ lưỡng từ Sơn La, Điện Biên, Lâm Đồng, Đắk Lắk, Kon Tum và Quảng Trị. Mỗi ly cà phê là hành trình khám phá hương vị đất đai Việt Nam.",
         tag="Tin Tức", emoji="☕", published_at="15/03/2026"),
    News(id=2, title="Sự Kiện Coffee Fest 2026 – Ngày Hội Cà Phê Lớn Nhất Năm",
         excerpt="Hàng nghìn tín đồ cà phê hội tụ tại Hà Nội trong 3 ngày trải nghiệm cà phê thủ công, hội thảo, và cuộc thi pha chế.",
         content="Coffee Fest 2026 diễn ra từ 20-22/04/2026 tại không gian ngoài trời Vincom Mega Mall Royal City, Hà Nội. Sự kiện quy tụ hơn 50 thương hiệu cà phê trong và ngoài nước, cùng các buổi workshop và cuộc thi barista quốc tế.",
         tag="Sự Kiện", emoji="🎉", published_at="10/03/2026"),
    News(id=3, title="Highlands Coffee Mở Thêm 20 Chi Nhánh Mới Trong Quý 2/2026",
         excerpt="Tiếp tục mở rộng mạng lưới, Highlands Coffee sẽ có mặt tại thêm 8 tỉnh thành với 20 địa điểm mới trong quý 2.",
         content="Trong chiến lược mở rộng 2026, Highlands Coffee lên kế hoạch khai trương 20 chi nhánh mới tại các tỉnh thành như Hải Phòng, Cần Thơ, Huế, Nha Trang, Vũng Tàu và các khu công nghiệp lớn. Mỗi chi nhánh đều được thiết kế theo phong cách hiện đại kết hợp văn hóa địa phương.",
         tag="Tin Tức", emoji="🏪", published_at="08/03/2026"),
    News(id=4, title="Khuyến Mãi Tháng 4 – Combo Tiết Kiệm Cho Nhóm Bạn",
         excerpt="Tháng 4 này, mua 3 ly bất kỳ chỉ với giá của 2 ly. Chương trình áp dụng toàn hệ thống từ ngày 01/04.",
         content="Tháng 4 là tháng của những cuộc gặp gỡ và chia sẻ. Highlands Coffee mang đến ưu đãi đặc biệt: Mua 3 Trả 2 áp dụng cho tất cả đồ uống trong menu, giúp bạn và bạn bè có những khoảnh khắc cà phê tuyệt vời hơn với chi phí tiết kiệm hơn.",
         tag="Khuyến Mãi", emoji="💰", published_at="01/04/2026"),
    News(id=5, title="Bí Quyết Pha Cà Phê Phin Ngon Chuẩn Vị Highlands",
         excerpt="Đội ngũ barista Highlands chia sẻ những bí quyết pha cà phê phin đúng cách để có ly cà phê hoàn hảo tại nhà.",
         content="Cà phê phin là linh hồn của văn hóa cà phê Việt Nam. Trong bài viết này, các chuyên gia barista của Highlands Coffee sẽ hướng dẫn từng bước: từ lựa chọn hạt cà phê rang vừa, tỉ lệ pha, nhiệt độ nước sôi đúng chuẩn cho đến cách thưởng thức để cảm nhận hết hương vị.",
         tag="Tin Tức", emoji="📖", published_at="05/03/2026"),
    News(id=6, title="Highlands Coffee Được Vinh Danh Top 3 Thương Hiệu Cà Phê Yêu Thích Nhất 2026",
         excerpt="Theo khảo sát của Vietnam Brand Awards 2026, Highlands Coffee nằm trong top 3 thương hiệu cà phê được người tiêu dùng Việt yêu thích nhất.",
         content="Vietnam Brand Awards 2026 vừa công bố kết quả khảo sát người tiêu dùng với hơn 100.000 phiếu bình chọn. Highlands Coffee xếp thứ 3 trong danh mục thương hiệu cà phê được yêu thích nhất, nhờ chất lượng sản phẩm ổn định, mạng lưới phủ rộng và chương trình khách hàng thân thiết hấp dẫn.",
         tag="Sự Kiện", emoji="🏆", published_at="01/03/2026"),
]


def seed():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Categories — must be seeded before products
        if db.query(Category).count() == 0:
            db.add_all(CATEGORIES)
            db.commit()
            print(f"Seeded {len(CATEGORIES)} categories.")
        else:
            print("Categories already seeded, skipping.")

        # Products
        if db.query(Product).count() == 0:
            db.add_all(PRODUCTS)
            db.commit()
            print(f"Seeded {len(PRODUCTS)} products.")
        else:
            print("Products already seeded, skipping.")

        # Stores
        if db.query(Store).count() == 0:
            db.add_all(STORES)
            db.commit()
            print(f"Seeded {len(STORES)} stores.")
        else:
            print("Stores already seeded, skipping.")

        # Promotions
        if db.query(Promotion).count() == 0:
            db.add_all(PROMOTIONS)
            db.commit()
            print(f"Seeded {len(PROMOTIONS)} promotions.")
        else:
            print("Promotions already seeded, skipping.")

        # News
        if db.query(News).count() == 0:
            db.add_all(NEWS)
            db.commit()
            print(f"Seeded {len(NEWS)} news articles.")
        else:
            print("News already seeded, skipping.")

    finally:
        db.close()
    print("Done.")


if __name__ == "__main__":
    seed()
