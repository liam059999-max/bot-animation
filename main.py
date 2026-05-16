# Script Discord corrigé (rôles + interactions)

```python
import discord
from discord import app_commands
from discord.ui import View, Button, Modal, TextInput
import os
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

GUILD_ID = 1498763331496837240

EVENT_CHANNEL_ID = 1498763332541219035
LOG_CHANNEL_ID = 1498763333057253415
TABLEAU_CHANNEL_ID = 1498763333057253413
COFFRE_CHANNEL_ID = 1498763333057253409

# Rôles réactions / animateurs
ANIMATEUR_ROLE_ID = 1498763331526328442
MOD_ANIM_ROLE_ID = 1498763331526328441
ANCIEN_ANIM_ROLE_ID = 1498763331496837249

# Rôles autorisés aux commandes admin
ADMIN_ROLES = [
    1498763331526328445,
    1498763331526328444,
    1498763331526328443
]

DATA_FILE = "animateurs.json"
COFFRE_FILE = "coffre_armes.json"


def load_json(file_path, default):
    if not os.path.exists(file_path):
        return default

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_json(file_path, data):
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        await self.tree.sync(guild=guild)

        # IMPORTANT POUR LES BOUTONS
        self.add_view(RapportView())

        print("✅ Commandes synchronisées")


client = MyClient()


@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")


class RapportModal(Modal):
    def __init__(self, type_rapport, emoji, couleur):
        super().__init__(title=type_rapport)

        self.type_rapport = type_rapport
        self.emoji = emoji
        self.couleur = couleur

        self.description_input = TextInput(
            label="Description",
            placeholder="Explique ce qu'il s'est passé...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        event_channel = interaction.guild.get_channel(EVENT_CHANNEL_ID)

        embed_event = discord.Embed(
            title=f"{self.emoji} {self.type_rapport}",
            description=(
                f"**Par :** {interaction.user.mention}\n\n"
                f"**Description :**\n{self.description_input.value}"
            ),
            color=self.couleur
        )

        await event_channel.send(embed=embed_event)

        await interaction.followup.send(
            "✅ Rapport envoyé avec succès.",
            ephemeral=True
        )


class RapportView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Début event",
        emoji="🟢",
        style=discord.ButtonStyle.success,
        custom_id="rapport_debut"
    )
    async def debut_event(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            RapportModal(
                "Début d'évènement",
                "🟢",
                discord.Color.green()
            )
        )

    @discord.ui.button(
        label="Fin event",
        emoji="🔴",
        style=discord.ButtonStyle.danger,
        custom_id="rapport_fin"
    )
    async def fin_event(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            RapportModal(
                "Fin d'évènement",
                "🔴",
                discord.Color.red()
            )
        )

    @discord.ui.button(
        label="Incident",
        emoji="⚠️",
        style=discord.ButtonStyle.secondary,
        custom_id="rapport_incident"
    )
    async def incident(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            RapportModal(
                "Incident",
                "⚠️",
                discord.Color.orange()
            )
        )

    @discord.ui.button(
        label="Autre",
        emoji="📝",
        style=discord.ButtonStyle.secondary,
        custom_id="rapport_autre"
    )
    async def autre(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            RapportModal(
                "Autre",
                "📝",
                discord.Color.blurple()
            )
        )


@client.tree.command(
    name="rapport",
    description="Envoie le panneau de rapport",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.has_any_role(*ADMIN_ROLES)
async def rapport(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Rapport d'évènement",
        description=(
            "Utilise les boutons ci-dessous pour signaler une action liée à un évènement.\n"
            "Chaque rapport est horodaté et enregistré.\n\n"
            "🟢 Début event — Signaler le lancement d'un évènement\n"
            "🔴 Fin event — Signaler la fin d'un évènement\n"
            "⚠️ Incident — Signaler un problème / incident\n"
            "📝 Autre — Rapport libre"
        ),
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(
        embed=embed,
        view=RapportView()
    )


@rapport.error
async def rapport_error(interaction: discord.Interaction, error):
    if interaction.response.is_done():
        await interaction.followup.send(
            "❌ Tu n’as pas la permission ou une erreur est survenue.",
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            "❌ Tu n’as pas la permission ou une erreur est survenue.",
            ephemeral=True
        )


client.run(TOKEN)
```
