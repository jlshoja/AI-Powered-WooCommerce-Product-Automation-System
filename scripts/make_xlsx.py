import pandas as pd
from pathlib import Path

input_csv = Path('input/Product_Master.csv')
output_xlsx = Path('output/Product_Master_v2.xlsx')

df = pd.read_csv(input_csv)
products = df[df['post_type'] == 'product'].copy()
products['ID'] = [f'prod_{i}' for i in range(len(products))]
products['stock_status'] = 'instock'

def get_main_local(val):
    filenames = str(val).split('|') if pd.notna(val) else []
    return filenames[0] if filenames else ''

def get_gallery_locals(val):
    filenames = str(val).split('|') if pd.notna(val) else []
    return '|'.join(filenames[1:]) if len(filenames) > 1 else ''

products['local_image'] = products['image_filename'].apply(get_main_local)
products['local_gallery_images'] = products['image_filename'].apply(get_gallery_locals)

variations = df[df['post_type'] == 'product_variation'].copy()
variations['ID'] = [f'var_{i}' for i in range(len(variations))]
variations['stock_status'] = 'instock'

categories = products['categories'].str.split('>', expand=True).stack().reset_index(drop=True).unique()
categories_df = pd.DataFrame({
    'ID': [f'cat_{i}' for i in range(len(categories))],
    'name': categories,
    'parent_category': ''
})

attrs = {}
for col in df.columns:
    if col.startswith('attribute:'):
        attr_name = col.split(':')[1]
        values = df[col].dropna().unique()
        attrs[attr_name] = [str(v) for v in values]

attributes_df = pd.DataFrame([
    {'ID': f'attr_{i}', 'name': k, 'values': '|'.join(v)}
    for i, (k, v) in enumerate(attrs.items())
])

images_list = []

for _, row in products.iterrows():
    local_filenames = str(row.get('image_filename', '')).split('|') if pd.notna(row.get('image_filename', '')) else []
    main_local = local_filenames[0] if local_filenames else ''
    gal_locals = local_filenames[1:] if len(local_filenames) > 1 else []

    if pd.notna(row['images']) and row['images'] != '':
        images_list.append({
            'ID': f"img_{row['ID']}_main",
            'product_sku': row['sku'],
            'image_url': row['images'],
            'alt_text': row.get('image_alt', ''),
            'title': row.get('image_titles', ''),
            'is_main': True,
            'local_filename': main_local
        })

    if pd.notna(row['gallery_images']) and row['gallery_images'] != '':
        gal_urls = row['gallery_images'].split('|')
        gal_alts = str(row.get('gallery_image_alt', '')).split('|') if pd.notna(row.get('gallery_image_alt', '')) else []
        gal_titles = str(row.get('image_titles', '')).split('|') if pd.notna(row.get('image_titles', '')) else []

        main_url = row.get('images', '')
        if gal_urls and gal_urls[0] == main_url:
            gal_urls = gal_urls[1:]
            gal_alts = gal_alts[1:] if gal_alts else []
            gal_titles = gal_titles[1:] if gal_titles else []

        for i, url in enumerate(gal_urls):
            images_list.append({
                'ID': f"img_{row['ID']}_gal_{i}",
                'product_sku': row['sku'],
                'image_url': url,
                'alt_text': gal_alts[i] if i < len(gal_alts) else '',
                'title': gal_titles[i] if i < len(gal_titles) else '',
                'is_main': False,
                'local_filename': gal_locals[i] if i < len(gal_locals) else ''
            })

for _, row in variations.iterrows():
    if pd.notna(row['images']) and row['images'] != '':
        images_list.append({
            'ID': f"img_{row['ID']}_main",
            'product_sku': row['sku'],
            'image_url': row['images'],
            'alt_text': row.get('image_alt', ''),
            'title': row.get('image_titles', ''),
            'is_main': True,
            'local_filename': ''
        })

with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
    products.to_excel(writer, sheet_name='Products', index=False)
    variations.to_excel(writer, sheet_name='Variations', index=False)
    categories_df.to_excel(writer, sheet_name='Categories', index=False)
    attributes_df.to_excel(writer, sheet_name='Attributes', index=False)
    pd.DataFrame(images_list).to_excel(writer, sheet_name='Images', index=False)

print('Product_Master_v2.xlsx created successfully!')
print(f'Products: {len(products)}')
print(f'Variations: {len(variations)}')
print(f'Categories: {len(categories_df)}')
print(f'Attributes: {len(attributes_df)}')
print(f'Images: {len(images_list)}')