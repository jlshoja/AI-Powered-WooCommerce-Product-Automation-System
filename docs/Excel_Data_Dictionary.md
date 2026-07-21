# Excel Data Dictionary

## Worksheets
| Worksheet    | Description                                                                                     |
|--------------|-------------------------------------------------------------------------------------------------|
| **Products** | Parent products (e.g., "کیف مردانه کد ۲۱۰۶").                                                   |
| **Variations** | Child products (e.g., "2106-green"). Linked to parents via `parent_sku`.                       |
| **Categories** | Hierarchical categories (e.g., "کیف مردانه > کیف روزمره مردانه").                              |
| **Attributes** | Product attributes (e.g., `رنگ`, `کاربرد`).                                                    |
| **Images**   | Image metadata (URLs, alt text, titles).                                                        |

## Fields (Products Worksheet)
| Field                     | Type       | Description                                                                                     | Example                          |
|---------------------------|------------|-------------------------------------------------------------------------------------------------|----------------------------------|
| `ID`                      | String     | Unique identifier for the product.                                                              | `a1b2c3d4-e5f6-7890`             |
| `post_title`              | String     | Product name (Persian).                                                                         | `کیف مردانه کد ۲۱۰۶`             |
| `sku`                     | String     | Unique SKU for the product.                                                                     | `2106`                           |
| `regular_price`           | Number     | Base price of the product.                                                                      | `342000`                         |
| `categories`              | String List| Hierarchical categories (pipe-separated).                                                       | `کیف مردانه>کیف روزمره مردانه`   |
| `images`                  | URL        | Main product image URL.                                                                         | `/uploads/2026/07/main.webp`     |
| `attributes:رنگ`          | String List| Attribute values (pipe-separated).                                                              | `سبز|سرمه ای|مشکی`             |
| `seo_title`               | String     | AI-generated SEO title (e.g., "کیف مردانه کد ۲۱۰۶ - خرید آنلاین با کیفیت بالا").               |                                  |
| `seo_description`         | String     | AI-generated SEO description.                                                                   |                                  |
| `tags`                    | String List| AI-generated tags (e.g., `["چرم", "کیف مردانه", "فروش ویژه"]`).                                 |                                  |