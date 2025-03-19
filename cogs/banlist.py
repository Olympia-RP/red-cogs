import discord
from redbot.core import commands, Config
import json

class Banlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=123456789)
        self.config.register_global(banlist={})

    async def on_member_ban(self, guild, user):
        # Récupérer la liste des bans existants
        banlist = await self.config.banlist()
        
        # Ajouter l'utilisateur banni à la liste avec des informations supplémentaires
        banlist[str(user.id)] = {
            "username": str(user),
            "guild": guild.name,
            "ban_time": str(guild.me.joined_at)  # Exemple de donnée supplémentaire
        }

        # Sauvegarder les données dans un fichier
        await self.config.banlist.set(banlist)
        print(f"Utilisateur {user} ajouté à la banlist.")

    @commands.command(name="showbanlist")
    async def show_banlist(self, ctx):
        """Afficher la liste des utilisateurs bannis"""
        banlist = await self.config.banlist()
        if not banlist:
            await ctx.send("Aucun utilisateur banni.")
        else:
            ban_info = ""
            for user_id, details in banlist.items():
                ban_info += f"**{details['username']}** banni sur {details['guild']} à {details['ban_time']}\n"
            await ctx.send(ban_info)

def setup(bot):
    bot.add_cog(Banlist(bot))  # Pas besoin de await ici
