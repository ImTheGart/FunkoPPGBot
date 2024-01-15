import discord
import requests
from discord.ext import commands
from discord.ui import Button, View
from bs4 import BeautifulSoup

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
header = {
    "user-agent": "Mozilla/5.0",
    'referer': 'https://www.google.com/'
}


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        await bot.tree.sync()
        print("Synced application commands with Discord")
    except Exception as e:
        print(e)


class ProductView(View):
    def __init__(self, products, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.products = products
        self.current_index = 0
        # Add buttons for navigation
        self.add_item(Button(label="Previous", style=discord.ButtonStyle.grey, custom_id="previous"))
        self.add_item(Button(label="Next", style=discord.ButtonStyle.grey, custom_id="next"))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Update the embed based on the button clicked
        if interaction.data.custom_id == "next":
            self.current_index = (self.current_index + 1) % len(self.products)
        elif interaction.data.custom_id == "previous":
            self.current_index = (self.current_index - 1) % len(self.products)

        new_embed = discord.Embed(title=self.products[self.current_index]['name'])
        new_embed.add_field(name="Price", value=self.products[self.current_index]['price'])
        new_embed.set_image(url=self.products[self.current_index]['image'])
        new_embed.add_field(name="Link", value=self.products[self.current_index]['url'])
        await interaction.response.edit_message(embed=new_embed, view=self)


@bot.tree.command(name="ppg", description="Fetch product info from PPG")
async def ppg(ctx, product_name: str):
    products = scrape_product_info(product_name)
    if products:
        view = ProductView(products)
        first_product = products[0]
        embed = discord.Embed(title=first_product['name'])
        embed.add_field(name="Price", value=first_product['price'])
        embed.set_image(url=first_product['image'])
        embed.add_field(name="Link", value=first_product['url'])
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send("Products not found.")


def scrape_product_info(product_name):
    search_url = f'https://www.hobbydb.com/marketplaces/poppriceguide/catalog_items?filters[q][0]={product_name}'
    print(f"Searching URL: {search_url}")  # Debug URL

    response = requests.get(search_url)
    if response.status_code != 200:
        print(f"Failed to fetch the webpage, status code: {response.status_code}")  # Debug HTTP response
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    # Finding the container of product cards
    products_container = soup.find('div', class_='col-xs-12')
    if not products_container:
        print("Products container not found")
        return []

    # Assuming each product card is a div inside 'products_container'
    product_cards = products_container.find_all('div', class_='catalog-item-card ng-scope',
                                                recursive=False)  # Adjust the 'div' if the product cards use a different tag
    if not product_cards:
        print("No product cards found")
        return []

    print(f"Found {len(product_cards)} product cards")

    products = []
    for card in product_cards:
        name_element = card.find('a', class_='catalog-item-name')
        price_element = card.find('div', class_='price-guide')
        image_element = card.find('img', src=True)

        if name_element:
            product_name = name_element.text.strip()
            print(f"Product Name: {product_name}")  # Debug product name
        else:
            product_name = "No name"
            print("Product name not found")

        if price_element:
            product_price = price_element.text.strip()
            print(f"Product Price: {product_price}")  # Debug product price
        else:
            product_price = "No price"
            print("Product price not found")

        if image_element:
            product_image_url = image_element['src']
            print(f"Product Image URL: {product_image_url}")  # Debug product image URL
        else:
            product_image_url = "No image URL"
            print("Product image URL not found")

        product_url = 'https://www.hobbydb.com' + card.find('a', href=True)['href'] if card.find('a',
                                                                                                 href=True) else "No product URL"
        print(f"Product URL: {product_url}")  # Debug product URL

        products.append({
            'name': product_name,
            'price': product_price,
            'image': product_image_url,
            'url': product_url
        })

    return products


bot.run('BOT_TOKEN')
