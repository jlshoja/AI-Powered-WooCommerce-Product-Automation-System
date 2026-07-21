# WooCommerce REST API Integration

## Endpoints Used
| Endpoint                          | Method | Purpose                                                                                     |
|-----------------------------------|--------|---------------------------------------------------------------------------------------------|
| `/wp-json/wc/v3/products`         | POST   | Create a new product.                                                                       |
| `/wp-json/wc/v3/products/{id}`    | PUT    | Update an existing product.                                                                |
| `/wp-json/wc/v3/products/{id}`    | GET    | Retrieve a product.                                                                        |
| `/wp-json/wc/v3/products/{id}/variations` | POST | Create a variation for a variable product.                                                 |
| `/wp-json/wc/v3/media`            | POST   | Upload an image to WordPress.                                                              |

## Authentication
- **Consumer Key**: `ck_your_consumer_key`
- **Consumer Secret**: `cs_your_consumer_secret`
- Configured in `config/settings.yaml`.

## Payload Examples
### Create a Simple Product
```json
{
  "name": "کیف مردانه کد ۲۱۰۶",
  "type": "simple",
  "regular_price": "342000",
  "description": "کیف مردانه با طراحی مدرن...",
  "short_description": "کیف مردانه کد ۲۱۰۶ با کیفیت بالا.",
  "categories": [{"name": "کیف مردانه"}],
  "images": [{"src": "/uploads/2026/07/main.webp"}],
  "meta_data": [
    {"key": "_yoast_wpseo_title", "value": "کیف مردانه کد ۲۱۰۶ - خرید آنلاین با کیفیت بالا"},
    {"key": "_yoast_wpseo_metadesc", "value": "کیف مردانه کد ۲۱۰۶ با طراحی مدرن و کیفیت بالا..."}
  ]
}
```

### Create a Variation
```json
{
  "sku": "2106-green",
  "regular_price": "342000",
  "attributes": [{"name": "رنگ", "option": "سبز"}],
  "image": {"src": "/uploads/2026/07/green.webp"}
}
```