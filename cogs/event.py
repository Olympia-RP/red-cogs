import discord
from redbot.core import commands
import json
import os

# 🔹 Définition des IDs (⚠️ Remplace ces valeurs par les bons IDs)
EVENT_ROLE_ID = 1341120754468786238  # ID du rôle à attribuer
EVENT_LOG_CHANNEL_ID = 1341121057578553465  # ID du canal de logs

class EventCog(commands.Cog):
    """Cog pour gérer les événements Discord"""

    def __init__(self, bot):
        self.bot = bot
        self.active_event = None
        self.participants = []
        self.event_closed = False
        self.event_message_id = None
        self.event_data_file = '/home/container/cogs/event/event.json'

        # 🔹 Vérifier si le fichier existe, sinon le créer
        if not os.path.exists(self.event_data_file):
            with open(self.event_data_file, 'w') as file:
                json.dump({}, file)

        # 🔹 Charger les données au démarrage
        with open(self.event_data_file, 'r') as file:
            try:
                data = json.load(file)
                self.active_event = data.get('active_event')
                self.participants = data.get('participants', [])
                self.event_closed = data.get('event_closed', False)
                self.event_message_id = data.get('event_message_id')
                print("✅ Données des événements chargées depuis event.json")
            except json.JSONDecodeError:
                print("⚠️ Erreur de lecture du fichier event.json, réinitialisation...")
                self.save_event_data()

    def save_event_data(self):
        """Sauvegarde les données de l'événement"""
        data = {
            'active_event': self.active_event,
            'participants': self.participants,
            'event_closed': self.event_closed,
            'event_message_id': self.event_message_id
        }
        with open(self.event_data_file, 'w') as file:
            json.dump(data, file, indent=4)

    async def log_event(self, message):
        """Envoie un message dans le canal de logs"""
        channel = self.bot.get_channel(EVENT_LOG_CHANNEL_ID)
        if channel:
            await channel.send(f"📢 **Log d'événement** : {message}")

    async def update_event_embed(self, ctx):
        """Met à jour l'embed de l'événement avec la liste des participants"""
        if not self.event_message_id:
            return

        try:
            channel = ctx.channel
            message = await channel.fetch_message(self.event_message_id)

            embed = discord.Embed(
                title=f"📅 Événement en cours : {self.active_event}",
                description="Utilisez `!course` pour participer et `!uncourse` pour vous désinscrire.",
                color=0x00AE86
            )
            embed.add_field(name="📋 Participants :", value="\n".join([f"<@{p}>" for p in self.participants]) if self.participants else "Aucun participant.")
            embed.set_footer(text=f"Total participants : {len(self.participants)}")
            embed.set_image(url="https://media.discordapp.net/attachments/1326646434841231450/1326648120259645490/file-9xBvYQXn3N4XDDZRi5XZb1.webp?ex=67b59597&is=67b44417&hm=80714b7b98153a9bbb33d5b308afd46c9ddc2d022df5f2de1d21c1cbaade8f71&=&format=webp&width=671&height=671")

            await message.edit(embed=embed)

        except discord.NotFound:
            print("⚠️ Impossible de mettre à jour l'embed, message introuvable.")
        except discord.Forbidden:
            print("🚫 Impossible de modifier l'embed, permissions insuffisantes.")

    def is_admin(self, ctx):
        """Vérifie si l'utilisateur est administrateur"""
        return ctx.author.guild_permissions.administrator

    @commands.command()
    async def event(self, ctx, *args):
        """Commande principale pour gérer les événements"""
        print(f"🔹 Commande event exécutée avec args : {args}")

        if not args:
            await ctx.send("📌 Commandes disponibles :\n"
                           "`!event create <nom>` - Créer un événement\n"
                           "`!event delete` - Supprimer l'événement actif\n"
                           "`!event end` - Clôturer les inscriptions\n"
                           "`!event reopen` - Réouvrir les inscriptions")
            return

        sub_command = args[0].lower()

        # 🔹 Vérification des permissions pour les commandes admin
        if sub_command in ['create', 'delete', 'end', 'reopen'] and not self.is_admin(ctx):
            await ctx.send("🚫 Tu n'as pas la permission d'exécuter cette commande.")
            return

        if sub_command == 'create':
            if self.active_event:
                await ctx.send(f"❌ Un événement est déjà en cours : **{self.active_event}**")
                return

            self.active_event = ' '.join(args[1:])
            if not self.active_event:
                await ctx.send("⚠️ Tu dois spécifier un nom d'événement !")
                return

            self.participants = []
            self.event_closed = False
            self.save_event_data()

            embed = discord.Embed(
                title=f"📅 Événement en cours : {self.active_event}",
                description="Utilisez `!course` pour participer et `!uncourse` pour vous désinscrire.",
                color=0x00AE86
            )
            embed.add_field(name="📋 Participants :", value="Aucun participant.")
            embed.set_footer(text="Total participants : 0")
            embed.set_image(url="https://media.discordapp.net/attachments/1326646434841231450/1326648120259645490/file-9xBvYQXn3N4XDDZRi5XZb1.webp?ex=67b59597&is=67b44417&hm=80714b7b98153a9bbb33d5b308afd46c9ddc2d022df5f2de1d21c1cbaade8f71&=&format=webp&width=671&height=671")

            message = await ctx.send(embed=embed)
            self.event_message_id = message.id
            self.save_event_data()

            await self.log_event(f"🆕 **Événement créé** : {self.active_event} par {ctx.author.name}")
            await ctx.send(f"✅ Événement **{self.active_event}** créé !")

        elif sub_command == 'delete':
            if not self.active_event:
                await ctx.send("❌ Aucun événement actif.")
                return

            guild = ctx.guild
            event_role = guild.get_role(EVENT_ROLE_ID)

            if event_role:
                for user_id in self.participants:
                    member = guild.get_member(user_id)
                    if member:
                        await member.remove_roles(event_role)

            # Nettoyage du canal (supprime les messages récents)
            await ctx.channel.purge(limit=100, check=lambda m: not m.pinned)

            self.active_event = None
            self.participants = []
            self.event_closed = False
            self.event_message_id = None
            self.save_event_data()

            await self.log_event(f"🗑️ **Événement supprimé** par {ctx.author.name}")
            await ctx.send("🗑️ L'événement a été supprimé et les rôles des participants ont été retirés.")


        elif sub_command == 'end':
            if not self.active_event or self.event_closed:
                await ctx.send("❌ Aucun événement actif ou déjà clôturé.")
                return

            self.event_closed = True
            self.save_event_data()
            await self.log_event(f"🔒 **Inscriptions fermées** pour {self.active_event} par {ctx.author.name}")
            await ctx.send(f"🔒 Les inscriptions pour **{self.active_event}** sont fermées.")

        elif sub_command == 'reopen':
            if not self.active_event or not self.event_closed:
                await ctx.send("❌ Aucun événement actif ou inscriptions déjà ouvertes.")
                return

            self.event_closed = False
            self.save_event_data()
            await self.log_event(f"🔓 **Inscriptions rouvertes** pour {self.active_event} par {ctx.author.name}")
            await ctx.send(f"🔓 Les inscriptions pour **{self.active_event}** sont à nouveau ouvertes !")

    @commands.command()
    async def course(self, ctx):
        """Inscrire un participant à l'événement"""
        if not self.active_event:
            await ctx.send("❌ Aucun événement en cours.")
            return

        if self.event_closed:
            await ctx.send("❌ Les inscriptions sont fermées.")
            return

        if ctx.author.id in self.participants:
            await ctx.send("⚠️ Tu es déjà inscrit à cet événement !")
            return

        self.participants.append(ctx.author.id)
        self.save_event_data()
        await self.update_event_embed(ctx)  # Met à jour l'embed avec les nouveaux participants

        event_role = ctx.guild.get_role(EVENT_ROLE_ID)
        if event_role:
            await ctx.author.add_roles(event_role)

        await self.log_event(f"✅ {ctx.author.name} a rejoint **{self.active_event}**")
        await ctx.send(f"✅ {ctx.author.name} a rejoint **{self.active_event}** !")

    @commands.command()
    async def uncourse(self, ctx):
        """Désinscrire un participant de l'événement"""
        if not self.active_event:
            await ctx.send("❌ Aucun événement en cours.")
            return

        if ctx.author.id not in self.participants:
            await ctx.send("⚠️ Tu n'es pas inscrit à cet événement.")
            return

        self.participants.remove(ctx.author.id)
        self.save_event_data()
        await self.update_event_embed(ctx)  # Met à jour l'embed avec les nouveaux participants

        event_role = ctx.guild.get_role(EVENT_ROLE_ID)
        if event_role:
            await ctx.author.remove_roles(event_role)

        await self.log_event(f"❌ {ctx.author.name} a quitté **{self.active_event}**")
        await ctx.send(f"❌ {ctx.author.name} a quitté **{self.active_event}** !")
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if message.content.lower() in ["!course", "!uncourse", "!event"]:
            await message.delete()


# 🔹 **Correction pour Red-DiscordBot**
async def setup(bot):  
    await bot.add_cog(EventCog(bot))
