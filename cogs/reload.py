from redbot.core import commands

class ReloadCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def reloadcog(self, ctx, cog: str):
        """Recharge un module (cog) en le déchargeant puis en le rechargeant."""
        try:
            await ctx.invoke(self.bot.get_command("unload"), cog)
            await ctx.invoke(self.bot.get_command("load"), cog)
            await ctx.send(f"✅ Le module `{cog}` a été rechargé avec succès !")
        except Exception as e:
            await ctx.send(f"❌ Erreur lors du rechargement du module `{cog}` : {e}")

async def setup(bot):
    await bot.add_cog(ReloadCog(bot))  # Correction ici
