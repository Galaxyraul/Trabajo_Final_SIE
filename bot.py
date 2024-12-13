import procesador
from telegram.ext import Application, CommandHandler, MessageHandler, filters

mapa = procesador.Mapa()
PATH_KEY = './BOT_KEY.txt'
leyenda = f'Verde:Nivel de riesgo nulo,\n  Amarillo:Nivel de riesgo medio,\n Rojo:Nivel de riesgo alto,\nNegro::Nivel de riesgo muy alto'  
mensajes_nivel_riesgo = {
    0:"Riesgo Nulo:Alerta climatológica: No se esperan condiciones meteorológicas que puedan generar inundaciones. El riesgo de inundación es nulo. Manténgase informado sobre el pronóstico climático y siga las recomendaciones de las autoridades locales.",
    1:"Riesgo Medio:Alerta climatológica: Se prevé un aumento moderado en las lluvias en las próximas horas. Aunque el riesgo de inundación es bajo, se recomienda precaución en áreas propensas a acumulaciones de agua, especialmente en zonas urbanas con drenaje limitado. Manténgase alerta y consulte las actualizaciones meteorológicas.",
    2:"Riesgo Alto:Alerta climatológica: Se esperan lluvias intensas que podrían generar inundaciones en áreas bajas y en zonas de drenaje insuficiente. El riesgo de inundación es alto. Evite viajar por caminos rurales y áreas cercanas a ríos y arroyos. Si se encuentra en una zona de riesgo, prepárese para posibles evacuaciones y siga las indicaciones de las autoridades locales.",
    3:"Riesgo Muy Alto:\nAlerta climatológica: Se prevén lluvias torrenciales que podrían causar inundaciones graves. El riesgo de inundación es muy alto. Se recomienda evacuar áreas de alto riesgo de inundación y seguir las instrucciones de las autoridades de emergencia. Manténgase alejado de ríos, arroyos y áreas propensas a desbordamientos. La situación es crítica, y se insta a la población a tomar medidas de protección inmediatas",
}
mensaje_conjunto = "Riesgo Nulo:\nAlerta climatológica: No se esperan condiciones meteorológicas que puedan generar inundaciones. El riesgo de inundación es nulo. Manténgase informado sobre el pronóstico climático y siga las recomendaciones de las autoridades locales.\nRiesgo Medio:\nAlerta climatológica: Se prevé un aumento moderado en las lluvias en las próximas horas. Aunque el riesgo de inundación es bajo, se recomienda precaución en áreas propensas a acumulaciones de agua, especialmente en zonas urbanas con drenaje limitado. Manténgase alerta y consulte las actualizaciones meteorológicas.\nRiesgo Alto:\nAlerta climatológica: Se esperan lluvias intensas que podrían generar inundaciones en áreas bajas y en zonas de drenaje insuficiente. El riesgo de inundación es alto. Evite viajar por caminos rurales y áreas cercanas a ríos y arroyos. Si se encuentra en una zona de riesgo, prepárese para posibles evacuaciones y siga las indicaciones de las autoridades locales.\nRiesgo Muy Alto:\nAlerta climatológica: Se prevén lluvias torrenciales que podrían causar inundaciones graves. El riesgo de inundación es muy alto. Se recomienda evacuar áreas de alto riesgo de inundación y seguir las instrucciones de las autoridades de emergencia. Manténgase alejado de ríos, arroyos y áreas propensas a desbordamientos. La situación es crítica, y se insta a la población a tomar medidas de protección inmediatas"
with open (PATH_KEY,'r') as f:
    API_KEY = f.read()

async def start(update, context) -> None:
    await update.message.reply_text('Hello! I am your bot. How can I assist you today?')

async def help_command(update, context) -> None:
    await update.message.reply_text('Los comandos que puedes utilizar son:\n/start\n/help\n/municipio\n/Andalucia')


async def municipio(update, context) -> None:
    if not context.args:
        update.message.reply_text("Indica el nombre de un municipio")
        return

    municipio_name = ' '.join(context.args)
    image_path, riesgo = mapa.get_municipio(municipio_name)

    with open(image_path, 'rb') as img:
        await update.message.reply_photo(photo=img, caption=f"Mapa de riesgo para {municipio_name}")
    await update.message.reply_text(mensajes_nivel_riesgo[riesgo])

async def andalucia(update, context) -> None:
    image_path = mapa.get_andalucia()

    with open(image_path, 'rb') as img:
        await update.message.reply_photo(photo=img, caption=f"Mapa de riesgo para andalucía")
    await update.message.reply_text(leyenda)
    await update.message.reply_text(mensaje_conjunto)

async def municipio_risky(update, context) -> None:
    if not context.args:
        update.message.reply_text("Indica el nombre de un municipio")
        return
    print('Procesando m_risky')
    municipio_name = ' '.join(context.args)
    image_path, riesgo = mapa.get_municipio_risky(municipio_name)

    with open(image_path, 'rb') as img:
        await update.message.reply_photo(photo=img, caption=f"Mapa de riesgo para {municipio_name}")
    await update.message.reply_text(mensajes_nivel_riesgo[riesgo])

async def andalucia_risky(update, context) -> None:
    image_path = mapa.get_andalucia_risky()

    with open(image_path, 'rb') as img:
        await update.message.reply_photo(photo=img, caption=f"Mapa de riesgo para andalucía")
    await update.message.reply_text(leyenda)
    await update.message.reply_text(mensaje_conjunto)

def main():
    # Set up the Updater
    application = Application.builder().token(API_KEY).build()

    

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("municipio", municipio))
    application.add_handler(CommandHandler("Andalucia", andalucia))
    application.add_handler(CommandHandler("municipio_risky", municipio_risky))
    application.add_handler(CommandHandler("Andalucia_risky", andalucia_risky))
    # Start polling
    application.run_polling()
    print("Bot is running...")

if __name__ == '__main__':
    main()
