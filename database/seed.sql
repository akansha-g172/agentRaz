-- MERCHANTS

INSERT INTO merchants (
    name,
    description
)
VALUES (
    'TechNova Electronics',
    'AI-ready electronics store specializing in laptops, peripherals and developer accessories.'
);

-- BUYERS

INSERT INTO buyers (
    name,
    preferences,
    spending_limit
)
VALUES
(
    'Demo Buyer',
    '{
        "preferred_brands": ["Lenovo", "ASUS", "Logitech"],
        "use_cases": ["coding", "development"]
    }',
    70000
);

-- PRODUCTS

INSERT INTO products
(
    merchant_id,
    name,
    category,
    brand,
    description,
    price,
    specifications,
    use_cases
)
SELECT
    m.id,
    p.name,
    p.category,
    p.brand,
    p.description,
    p.price,
    p.specifications::jsonb,
    p.use_cases
FROM merchants m
CROSS JOIN (
    VALUES

    (
        'NovaBook Pro 14',
        'Laptop',
        'NovaTech',
        '14-inch developer laptop with strong performance and lightweight design.',
        64999,
        '{"ram":"16GB","storage":"512GB SSD","processor":"Intel Core i5","display":"14 inch FHD","weight":"1.45 kg"}',
        ARRAY['coding','software development','college','productivity']
    ),

    (
        'CodeMaster X15',
        'Laptop',
        'Lenovo',
        'Performance-focused laptop designed for software development.',
        68999,
        '{"ram":"16GB","storage":"1TB SSD","processor":"AMD Ryzen 7","display":"15.6 inch FHD","weight":"1.7 kg"}',
        ARRAY['coding','software development','machine learning']
    ),

    (
        'DevBook Air',
        'Laptop',
        'ASUS',
        'Slim laptop optimized for portability and development workflows.',
        59999,
        '{"ram":"16GB","storage":"512GB SSD","processor":"Intel Core i5","display":"14 inch FHD","weight":"1.3 kg"}',
        ARRAY['coding','college','travel','productivity']
    ),

    (
        'UltraDev 16',
        'Laptop',
        'Acer',
        'Large-screen development laptop with high memory capacity.',
        69999,
        '{"ram":"16GB","storage":"1TB SSD","processor":"Intel Core i7","display":"16 inch WUXGA","weight":"1.85 kg"}',
        ARRAY['coding','software development','machine learning']
    ),

    (
        'VisionMonitor 27',
        'Monitor',
        'Dell',
        '27-inch productivity monitor with Full HD resolution.',
        14999,
        '{"size":"27 inch","resolution":"1920x1080","refresh_rate":"75Hz","panel":"IPS"}',
        ARRAY['coding','productivity','design']
    ),

    (
        'ProView 24',
        'Monitor',
        'LG',
        '24-inch IPS monitor suitable for development and office work.',
        10999,
        '{"size":"24 inch","resolution":"1920x1080","refresh_rate":"75Hz","panel":"IPS"}',
        ARRAY['coding','productivity']
    ),

    (
        'MechKey K87',
        'Keyboard',
        'Keychron',
        'Compact mechanical keyboard for programmers.',
        4999,
        '{"layout":"87-key","switch":"Mechanical","connection":"Bluetooth + USB-C"}',
        ARRAY['coding','gaming','productivity']
    ),

    (
        'OfficeType Wireless',
        'Keyboard',
        'Logitech',
        'Wireless productivity keyboard with quiet keys.',
        2499,
        '{"connection":"Wireless","layout":"Full-size","battery":"24 months"}',
        ARRAY['productivity','office','coding']
    ),

    (
        'Precision Mouse MX',
        'Mouse',
        'Logitech',
        'Ergonomic wireless mouse for long development sessions.',
        2999,
        '{"connection":"Wireless","dpi":"4000","buttons":"7"}',
        ARRAY['coding','productivity','design']
    ),

    (
        'SwiftMouse M2',
        'Mouse',
        'NovaTech',
        'Lightweight wireless mouse for everyday use.',
        999,
        '{"connection":"Wireless","dpi":"1600","buttons":"5"}',
        ARRAY['coding','college','productivity']
    ),

    (
        'StudioHead Pro',
        'Headphones',
        'Sony',
        'Noise-cancelling headphones for focused work.',
        7999,
        '{"type":"Over-ear","noise_cancellation":"Active","connection":"Bluetooth"}',
        ARRAY['coding','travel','productivity']
    ),

    (
        'ClearVoice Headset',
        'Headphones',
        'JBL',
        'Wireless headset with microphone for meetings.',
        3499,
        '{"type":"Over-ear","microphone":"Built-in","connection":"Bluetooth"}',
        ARRAY['meetings','college','productivity']
    ),

    (
        'StreamCam HD',
        'Webcam',
        'Logitech',
        'Full HD webcam suitable for meetings and online presentations.',
        4999,
        '{"resolution":"1080p","fps":"30","microphone":"Dual"}',
        ARRAY['meetings','streaming','college']
    ),

    (
        'FastSSD 1TB',
        'Storage',
        'Samsung',
        'Portable high-speed 1TB SSD.',
        6999,
        '{"capacity":"1TB","interface":"USB-C","read_speed":"1050 MB/s"}',
        ARRAY['storage','development','backup']
    ),

    (
        'USB Hub 7-in-1',
        'Accessory',
        'Anker',
        'USB-C hub with multiple ports for modern laptops.',
        2999,
        '{"ports":"7","interface":"USB-C","hdmi":"Yes"}',
        ARRAY['laptops','productivity','development']
    ),

    (
        'Laptop Sleeve 14',
        'Accessory',
        'Targus',
        'Protective sleeve for 14-inch laptops.',
        1499,
        '{"size":"14 inch","material":"Water resistant fabric"}',
        ARRAY['laptops','travel','college']
    )

) AS p(
    name,
    category,
    brand,
    description,
    price,
    specifications,
    use_cases
)
WHERE m.name = 'TechNova Electronics';

-- INVENTORY

INSERT INTO inventory (
    product_id,
    stock_quantity
)
SELECT
    id,
    CASE
        WHEN category = 'Laptop' THEN 20
        WHEN category = 'Monitor' THEN 35
        WHEN category = 'Keyboard' THEN 50
        WHEN category = 'Mouse' THEN 80
        WHEN category = 'Headphones' THEN 40
        WHEN category = 'Webcam' THEN 30
        WHEN category = 'Storage' THEN 45
        ELSE 60
    END
FROM products;

-- MERCHANT POLICY

INSERT INTO merchant_policies (
    merchant_id,
    max_transaction_amount,
    max_discount_percent,
    max_retry_attempts,
    allow_upsell,
    require_confirmation_above
)
SELECT
    id,
    70000,
    10,
    1,
    TRUE,
    50000
FROM merchants
WHERE name = 'TechNova Electronics';

-- PRODUCT RELATIONSHIPS (upsell / cross-sell / frequently bought)

INSERT INTO product_relationships (
    product_id,
    related_product_id,
    relationship_type,
    confidence
)
SELECT
    lp.id,
    rp.id,
    rel.relationship_type,
    rel.confidence
FROM products lp
JOIN (
    VALUES
        ('NovaBook Pro 14', 'SwiftMouse M2', 'frequently_bought', 0.42),
        ('NovaBook Pro 14', 'USB Hub 7-in-1', 'compatible_with', 0.38),
        ('NovaBook Pro 14', 'Laptop Sleeve 14', 'cross_sell', 0.31),
        ('NovaBook Pro 14', 'FastSSD 1TB', 'upsell', 0.27),
        ('CodeMaster X15', 'Precision Mouse MX', 'frequently_bought', 0.45),
        ('CodeMaster X15', 'USB Hub 7-in-1', 'compatible_with', 0.36),
        ('CodeMaster X15', 'Laptop Sleeve 14', 'cross_sell', 0.29),
        ('DevBook Air', 'SwiftMouse M2', 'frequently_bought', 0.40),
        ('DevBook Air', 'Laptop Sleeve 14', 'cross_sell', 0.35),
        ('DevBook Air', 'USB Hub 7-in-1', 'compatible_with', 0.33),
        ('UltraDev 16', 'VisionMonitor 27', 'upsell', 0.30),
        ('UltraDev 16', 'Precision Mouse MX', 'frequently_bought', 0.28)
) AS rel(laptop_name, related_name, relationship_type, confidence)
    ON lp.name = rel.laptop_name
JOIN products rp ON rp.name = rel.related_name
WHERE lp.category = 'Laptop'
ON CONFLICT (product_id, related_product_id, relationship_type) DO NOTHING;