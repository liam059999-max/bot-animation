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

ANIMATEUR_ROLE_ID = 1498763331496837249
GERANT_ANIM_ROLE_ID = 1498763331526328443

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


def load_data():
    return load_json(DATA_FILE, {"message_id": None, "animateurs": {}})


def save_data(data):
    save_json(DATA_FILE, data)


def load_coffre():
    return load_json(COFFRE_FILE, {"message_id": None, "armes": []})


def save_coffre(data):
    save_json(COFFRE_FILE, data)


def get_role_display(member: discord.Member, guild: discord.Guild):
    if not member:
        return "@rôle inconnu"

    gerant_role = guild.get_role(GERANT_ANIM_ROLE_ID)
    anim_role = guild.get_role(ANIMATEUR_ROLE_ID)

    if gerant_role and gerant_role in member.roles:
        return gerant_role.mention

    if anim_role and anim_role in member.roles:
        return anim_role.mention

    return "@rôle inconnu"


async def send_log(interaction: discord.Interaction, action: str, details: str):
    log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
    if not log_channel:
        return

    embed = discord.Embed(
        title="ℹ️ Log",
        description=(
            f"**Action :** `{action}`\n"
            f"**Par :** {interaction.user.mention} ({interaction.user.name})\n"
            f"**Nom Discord :** `{interaction.user.display_name}`\n"
            f"**Détails :** {details}"
        ),
        color=discord.Color.from_rgb(88, 101, 242)
    )
    embed.set_footer(text=f"Nebulix — Logs Commandes • #{interaction.channel.name}")

    await log_channel.send(embed=embed)


async def update_tableau(guild: discord.Guild):
    data = load_data()
    channel = guild.get_channel(TABLEAU_CHANNEL_ID)

    if not channel:
        return

    animateurs = data.get("animateurs", {})

    if not animateurs:
        description = "Aucun animateur enregistré."
    else:
        lignes = []

        for index, (user_id, info) in enumerate(animateurs.items(), start=1):
            member = guild.get_member(int(user_id))
            mention = member.mention if member else f"<@{user_id}>"
            role_display = get_role_display(member, guild)

            lignes.append(
                f"**{index}.** {mention} — `{info.get('license', 'Aucune')}`\n"
                f"**Rôle :** {role_display}\n"
                f"**Sanctions :** {info.get('sanctions', 0)} | "
                f"**Notes :** {info.get('notes', 0)} | "
                f"**Rapports :** {info.get('rapports', 0)}"
            )

        description = "\n\n".join(lignes)

    embed = discord.Embed(
        title=f"📋 Liste des animateurs ({len(animateurs)})",
        description=description,
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Nebulix — Tableau Animateurs")

    message_id = data.get("message_id")

    try:
        if message_id:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
        else:
            message = await channel.send(embed=embed)
            data["message_id"] = message.id
            save_data(data)

    except discord.NotFound:
        message = await channel.send(embed=embed)
        data["message_id"] = message.id
        save_data(data)


async def update_coffre(guild: discord.Guild):
    data = load_coffre()
    channel = guild.get_channel(COFFRE_CHANNEL_ID)

    if not channel:
        return

    armes = data.get("armes", [])

    if not armes:
        description = "Aucune arme enregistrée dans le coffre."
    else:
        description = ""

        for arme in armes:
            status = arme.get("status", "dans le coffre")
            emoji = "🟢" if status == "dans le coffre" else "🔴"

            description += (
                f"{emoji} 🔫 **{arme.get('type', 'Inconnu')}** — "
                f"`{arme.get('license', 'Aucune')}` ({status})\n"
            )

    embed = discord.Embed(
        title=f"🔒 Contenu du coffre ({len(armes)} objets)",
        description=description,
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Nebulix — Gestion Animateurs")

    message_id = data.get("message_id")

    try:
        if message_id:
            message = await channel.fetch_message(message_id)
            await message.edit(embed=embed)
        else:
            message = await channel.send(embed=embed)
            data["message_id"] = message.id
            save_coffre(data)

    except discord.NotFound:
        message = await channel.send(embed=embed)
        data["message_id"] = message.id
        save_coffre(data)


class MyClient(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True

        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        guild = discord.Object(id=GUILD_ID)
        await self.tree.sync(guild=guild)
        print("✅ Commandes synchronisées")


client = MyClient()


@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")


@client.tree.interaction_check
async def interaction_check(interaction: discord.Interaction):
    return True


class RapportModal(Modal):
    def __init__(self, type_rapport, emoji, couleur, action):
        super().__init__(title=type_rapport)

        self.type_rapport = type_rapport
        self.emoji = emoji
        self.couleur = couleur
        self.action = action

        self.description = TextInput(
            label="Description",
            placeholder="Explique ce qu'il s'est passé...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )

        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        event_channel = interaction.guild.get_channel(EVENT_CHANNEL_ID)

        data = load_data()
        user_id = str(interaction.user.id)

        if user_id in data["animateurs"]:
            data["animateurs"][user_id]["rapports"] += 1
            save_data(data)
            await update_tableau(interaction.guild)

        if event_channel:
            embed_event = discord.Embed(
                title=f"{self.emoji} {self.type_rapport}",
                description=(
                    f"**Par :**\n{interaction.user.mention}\n\n"
                    f"**Description :**\n{self.description.value}"
                ),
                color=self.couleur
            )
            embed_event.set_footer(
                text=f"Nebulix — Gestion Animateurs • #{interaction.channel.name}"
            )

            await event_channel.send(embed=embed_event)

        await interaction.followup.send(
            embed=discord.Embed(
                title="✅ Rapport enregistré",
                description=f"Ton rapport **{self.type_rapport}** a été enregistré.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

        await send_log(
            interaction,
            f"eventreport.{self.action}",
            f"{self.type_rapport} — {self.description.value}"
        )


class RapportView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Début event", emoji="🟢", style=discord.ButtonStyle.success)
    async def debut_event(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            RapportModal("Début d'évènement", "🟢", discord.Color.green(), "debut_event")
        )

    @discord.ui.button(label="Fin event", emoji="🔴", style=discord.ButtonStyle.danger)
    async def fin_event(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            RapportModal("Fin event", "🔴", discord.Color.red(), "fin_event")
        )

    @discord.ui.button(label="Incident", emoji="⚠️", style=discord.ButtonStyle.secondary)
    async def incident(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            RapportModal("Incident", "⚠️", discord.Color.orange(), "incident")
        )

    @discord.ui.button(label="Autre", emoji="📝", style=discord.ButtonStyle.secondary)
    async def autre(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(
            RapportModal("Autre", "📝", discord.Color.blurple(), "autre")
        )


@client.tree.command(
    name="rapport",
    description="Envoie le panneau de rapport d'évènement",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.has_role(GERANT_ANIM_ROLE_ID)
async def rapport(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Rapport d'évènement",
        description=(
            "Utilise les boutons ci-dessous pour signaler une action liée à un évènement.\n"
            "Chaque rapport est horodaté et enregistré.\n\n"
            "🟢 **Début event** — Signaler le lancement d'un évènement\n"
            "🔴 **Fin event** — Signaler la fin d'un évènement\n"
            "⚠️ **Incident** — Signaler un problème / incident\n"
            "📝 **Autre** — Rapport libre"
        ),
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(embed=embed, view=RapportView())
    await send_log(interaction, "command.rapport", "/rapport")


@client.tree.command(
    name="add-animateur",
    description="Ajoute un animateur au tableau",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    membre="Animateur à ajouter",
    license_gta="License GTA du joueur"
)
@app_commands.checks.has_role(GERANT_ANIM_ROLE_ID)
async def add_animateur(interaction: discord.Interaction, membre: discord.Member, license_gta: str):
    await interaction.response.defer(ephemeral=True)

    role = interaction.guild.get_role(ANIMATEUR_ROLE_ID)
    if role and role not in membre.roles:
        await membre.add_roles(role, reason=f"Ajout tableau animateur par {interaction.user}")

    data = load_data()
    data["animateurs"][str(membre.id)] = {
        "license": license_gta,
        "sanctions": 0,
        "notes": 0,
        "rapports": 0
    }

    save_data(data)
    await update_tableau(interaction.guild)

    await interaction.followup.send(
        f"✅ {membre.mention} ajouté au tableau avec la license `{license_gta}`.",
        ephemeral=True
    )

    await send_log(
        interaction,
        "command.add_animateur",
        f"Membre : {membre.mention} — License : {license_gta}"
    )


@client.tree.command(
    name="retrait-liste-animateur",
    description="Retire un animateur du tableau",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(membre="Animateur à retirer")
@app_commands.checks.has_role(GERANT_ANIM_ROLE_ID)
async def retrait_liste_animateur(interaction: discord.Interaction, membre: discord.Member):
    await interaction.response.defer(ephemeral=True)

    data = load_data()
    user_id = str(membre.id)

    if user_id not in data["animateurs"]:
        await interaction.followup.send("❌ Ce membre n'est pas dans le tableau.", ephemeral=True)
        return

    del data["animateurs"][user_id]
    save_data(data)
    await update_tableau(interaction.guild)

    await interaction.followup.send(f"✅ {membre.mention} retiré du tableau.", ephemeral=True)

    await send_log(
        interaction,
        "command.retrait_liste_animateur",
        f"Membre : {membre.mention}"
    )


@client.tree.command(
    name="liste-animateur",
    description="Actualise le tableau animateurs",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.has_role(GERANT_ANIM_ROLE_ID)
async def liste_animateur(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    await update_tableau(interaction.guild)

    await interaction.followup.send("✅ Liste animateur actualisée.", ephemeral=True)

    await send_log(
        interaction,
        "command.liste_animateur",
        "Actualisation tableau animateurs"
    )


@client.tree.command(
    name="ajout-armes",
    description="Ajoute une arme officielle au coffre",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    type_arme="Type de l'arme",
    license_gta="License GTA de l'arme"
)
@app_commands.checks.has_role(GERANT_ANIM_ROLE_ID)
async def ajout_armes(interaction: discord.Interaction, type_arme: str, license_gta: str):
    await interaction.response.defer(ephemeral=True)

    data = load_coffre()

    data["armes"].append({
        "type": type_arme,
        "license": license_gta,
        "status": "dans le coffre",
        "added_by": interaction.user.id,
        "taken_by": None
    })

    save_coffre(data)
    await update_coffre(interaction.guild)

    await interaction.followup.send(
        f"✅ Arme ajoutée officiellement : **{type_arme}** — `{license_gta}`.",
        ephemeral=True
    )

    await send_log(
        interaction,
        "command.ajout_armes",
        f"Type : {type_arme} — License : {license_gta}"
    )


@client.tree.command(
    name="depot-armes",
    description="Remet une arme officielle dans le coffre",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(license_gta="License GTA de l'arme")
@app_commands.checks.has_any_role(ANIMATEUR_ROLE_ID, GERANT_ANIM_ROLE_ID)
async def depot_armes(interaction: discord.Interaction, license_gta: str):
    await interaction.response.defer(ephemeral=True)

    data = load_coffre()
    arme_trouvee = None

    for arme_item in data["armes"]:
        if arme_item.get("license") == license_gta:
            arme_trouvee = arme_item
            break

    if not arme_trouvee:
        await interaction.followup.send(
            "❌ License introuvable. Cette arme doit d'abord être ajoutée par un gérant avec `/ajout-armes`.",
            ephemeral=True
        )
        return

    if arme_trouvee.get("status") == "dans le coffre":
        await interaction.followup.send("❌ Cette arme est déjà dans le coffre.", ephemeral=True)
        return

    arme_trouvee["status"] = "dans le coffre"
    arme_trouvee["added_by"] = interaction.user.id
    arme_trouvee["taken_by"] = None

    save_coffre(data)
    await update_coffre(interaction.guild)

    await interaction.followup.send(
        f"✅ Arme remise dans le coffre : **{arme_trouvee.get('type')}** — `{license_gta}`.",
        ephemeral=True
    )

    await send_log(
        interaction,
        "command.depot_armes",
        f"License : {license_gta} — Arme : {arme_trouvee.get('type')}"
    )


@client.tree.command(
    name="retrait-armes",
    description="Sort une arme officielle du coffre",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(license_gta="License GTA de l'arme")
@app_commands.checks.has_any_role(ANIMATEUR_ROLE_ID, GERANT_ANIM_ROLE_ID)
async def retrait_armes(interaction: discord.Interaction, license_gta: str):
    await interaction.response.defer(ephemeral=True)

    data = load_coffre()
    arme_trouvee = None

    for arme_item in data["armes"]:
        if arme_item.get("license") == license_gta:
            arme_trouvee = arme_item
            break

    if not arme_trouvee:
        await interaction.followup.send("❌ License introuvable. Cette arme n'existe pas.", ephemeral=True)
        return

    if arme_trouvee.get("status") == "sorti":
        await interaction.followup.send("❌ Cette arme est déjà sortie.", ephemeral=True)
        return

    arme_trouvee["status"] = "sorti"
    arme_trouvee["taken_by"] = interaction.user.id

    save_coffre(data)
    await update_coffre(interaction.guild)

    await interaction.followup.send(
        f"✅ Arme sortie du coffre : **{arme_trouvee.get('type')}** — `{license_gta}`.",
        ephemeral=True
    )

    await send_log(
        interaction,
        "command.retrait_armes",
        f"License : {license_gta} — Arme : {arme_trouvee.get('type')}"
    )


@client.tree.command(
    name="delete-armes",
    description="Supprime définitivement une arme du coffre",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(license_gta="License GTA de l'arme à supprimer")
@app_commands.checks.has_role(GERANT_ANIM_ROLE_ID)
async def delete_armes(interaction: discord.Interaction, license_gta: str):
    await interaction.response.defer(ephemeral=True)

    data = load_coffre()

    arme_trouvee = None

    for arme in data["armes"]:
        if arme.get("license") == license_gta:
            arme_trouvee = arme
            break

    if not arme_trouvee:
        await interaction.followup.send(
            f"❌ Aucune arme trouvée avec la license `{license_gta}`.",
            ephemeral=True
        )
        return

    data["armes"].remove(arme_trouvee)

    save_coffre(data)
    await update_coffre(interaction.guild)

    await interaction.followup.send(
        f"🗑️ Arme supprimée définitivement : **{arme_trouvee.get('type')}** — `{license_gta}`.",
        ephemeral=True
    )

    await send_log(
        interaction,
        "command.delete_armes",
        f"Arme supprimée définitivement — {arme_trouvee.get('type')} — {license_gta}"
    )


@client.tree.command(
    name="liste-coffre",
    description="Actualise le tableau du coffre",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.checks.has_role(GERANT_ANIM_ROLE_ID)
async def liste_coffre(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    await update_coffre(interaction.guild)

    await interaction.followup.send("✅ Liste coffre actualisée.", ephemeral=True)

    await send_log(
        interaction,
        "command.liste_coffre",
        "Actualisation coffre"
    )


@client.tree.command(
    name="demote",
    description="Retire les rôles d'un membre et le supprime du tableau",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    membre="Membre à demote",
    raison="Raison du demote"
)
@app_commands.checks.has_role(GERANT_ANIM_ROLE_ID)
async def demote(interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison donnée"):
    await interaction.response.defer(ephemeral=True)

    if membre == interaction.user:
        await interaction.followup.send("❌ Tu ne peux pas te demote toi-même.", ephemeral=True)
        return

    if membre == interaction.guild.owner:
        await interaction.followup.send("❌ Tu ne peux pas demote le propriétaire.", ephemeral=True)
        return

    if membre.top_role >= interaction.guild.me.top_role:
        await interaction.followup.send("❌ Mon rôle est trop bas pour retirer ses rôles.", ephemeral=True)
        return

    roles_a_retirer = [
        role for role in membre.roles
        if role != interaction.guild.default_role and role < interaction.guild.me.top_role
    ]

    try:
        if roles_a_retirer:
            await membre.remove_roles(
                *roles_a_retirer,
                reason=f"Demote par {interaction.user} - {raison}"
            )

        data = load_data()
        user_id = str(membre.id)
        removed_from_tableau = False

        if user_id in data["animateurs"]:
            del data["animateurs"][user_id]
            removed_from_tableau = True
            save_data(data)
            await update_tableau(interaction.guild)

        await interaction.followup.send(
            f"✅ {membre.mention} a été demote.\n"
            f"🧹 Rôles retirés : {len(roles_a_retirer)}\n"
            f"📋 Supprimé du tableau : {'Oui' if removed_from_tableau else 'Non'}\n"
            f"📄 Raison : {raison}",
            ephemeral=True
        )

        await send_log(
            interaction,
            "command.demote",
            (
                f"Membre : {membre.mention} — rôles retirés : {len(roles_a_retirer)} "
                f"— tableau supprimé : {'oui' if removed_from_tableau else 'non'} "
                f"— raison : {raison}"
            )
        )

    except discord.Forbidden:
        await interaction.followup.send("❌ Je n’ai pas les permissions nécessaires.", ephemeral=True)

    except discord.HTTPException:
        await interaction.followup.send("❌ Une erreur Discord est survenue.", ephemeral=True)


@rapport.error
@ajout_armes.error
@depot_armes.error
@retrait_armes.error
@delete_armes.error
@demote.error
@add_animateur.error
@retrait_liste_animateur.error
@liste_animateur.error
@liste_coffre.error
async def command_error(interaction: discord.Interaction, error):
    message = "❌ Tu n’as pas la permission ou une erreur est survenue."

    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


client.run(TOKEN)