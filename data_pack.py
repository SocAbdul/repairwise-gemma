# RepairWise Gemma — Data Pack
# Knowledge base, multilingual templates, visual categories
# Generated from V17 notebook

# RepairWise V13 data pack: local knowledge + multilingual templates.
# This cell contains data only. All functions are defined once in the next engine cell.

LOCAL_KNOWLEDGE = [{'id': 'scam_bank_sms_privacy',
  'category': 'scam_phishing',
  'risk': 'HIGH',
  'topic': 'sms bank link card pin password otp phishing bizum account verify banco tarjeta contraseña codigo enlace '
           'estafa',
  'aliases': ['sms banco', 'bank link', 'card details', 'otp', 'pin', 'bizum', 'tarjeta', 'cuenta bloqueada'],
  'text': 'Banks and trusted companies do not ask for card numbers, PINs, passwords, OTP/SMS codes, or banking '
          'credentials through SMS links. The safe action is not to open the link, not to enter data, and to verify '
          'through the official app, official website, or the phone number printed on the bank card. If the user '
          'already entered data, they should contact the bank immediately, block the card, and change passwords from '
          'official channels.'},
 {'id': 'battery_swollen_safety',
  'category': 'battery_safety',
  'risk': 'HIGH',
  'topic': 'battery swollen hot overheating fire smell screen lifting bateria hinchada inflada caliente olor pantalla '
           'levantada',
  'aliases': ['bateria hinchada', 'battery swollen', 'screen lifting', 'pantalla levantada', 'inflada', 'huele raro'],
  'text': 'A swollen or overheating battery is a safety risk. The phone should not be charged, pressed, punctured, or '
          'used until inspected. Visible screen lifting, unusual smell, heat, or separation of the frame are warning '
          'signs. Keep the device away from heat and flammable materials.'},
 {'id': 'water_damage_salt_corrosion',
  'category': 'water_damage',
  'risk': 'HIGH',
  'topic': 'water liquid wet sea beach pool rain tea coffee humidity agua mojado playa mar piscina lluvia liquido '
           'salitre humedad cafe te',
  'aliases': ['se mojo', 'mojado', 'water', 'fell in water', 'playa', 'mar', 'piscina', 'salitre', 'liquid damage'],
  'text': 'After water, sea water, pool water, rain, tea, coffee, or any liquid damage, charging can create a short '
          'circuit. The safe action is to stop charging, power off if possible, dry only the exterior, avoid direct '
          'heat or rice, and get professional inspection. Sea water and salt can corrode internal components quickly.'},
 {'id': 'charging_port_basic',
  'category': 'charging_issue',
  'risk': 'MEDIUM',
  'topic': 'charging port cable charger slow not charging connector dirty loose no carga puerto cargador bateria '
           'porcentaje carga lenta',
  'aliases': ['no carga',
              'not charging',
              'charging port',
              'cargador',
              'cable',
              'puerto',
              'carga lenta',
              'nu se incarca',
              'nu se încarcă',
              'incarca',
              'încarcă'],
  'text': 'Charging issues are often caused by a dirty or damaged charging port, faulty cable, faulty charger, '
          'software issue, or worn battery. Try a different certified cable and charger first. Do not force the '
          'connector and do not insert metal objects into the port.'},
 {'id': 'screen_display_touch',
  'category': 'screen_repair',
  'risk': 'MEDIUM',
  'topic': 'screen cracked broken display touch glass lines black spots green line pantalla rota tactil cristal lineas '
           'negra verde manchas',
  'aliases': ['pantalla rota',
              'cracked screen',
              'black screen',
              'green line',
              'touch not working',
              'lineas',
              'manchas'],
  'text': 'Screen damage can affect glass, display/OLED/LCD, touch, or internal flex cables. Cracks can spread, glass '
          'can cut, and lines/black spots can worsen. Backup data if the phone still works and avoid pressing the '
          'display.'},
 {'id': 'boot_logo_data_risk',
  'category': 'boot_issue',
  'risk': 'MEDIUM',
  'topic': 'boot bootloop logo stuck restart power on off frozen no enciende reinicia logo apagado prende dead phone',
  'aliases': ['no enciende', 'bootloop', 'stuck logo', 'se reinicia', 'logo', 'dead phone', 'no prende'],
  'text': 'A phone stuck on the logo, restarting, or not turning on may have corrupted software, full storage, battery '
          'failure, or hardware failure. A forced restart can help, but factory reset can erase data, so data backup '
          'must be considered first.'},
 {'id': 'audio_speaker_microphone_calls',
  'category': 'audio_issue',
  'risk': 'LOW',
  'topic': 'sound audio speaker microphone call volume earpiece no se escucha altavoz microfono llamada volumen '
           'auricular',
  'aliases': ['altavoz', 'speaker', 'microfono', 'microphone', 'no me escuchan', 'call audio', 'auricular'],
  'text': 'Audio issues can come from dirt in speaker or microphone grilles, Bluetooth routing, volume settings, '
          'software bugs, water damage, or damaged parts. Basic checks include turning Bluetooth off, testing voice '
          'recorder, testing speakerphone, and checking volume.'},
 {'id': 'camera_black_blurry_permissions',
  'category': 'camera_issue',
  'risk': 'LOW',
  'topic': 'camera photo blurry black not working focus flash lens permission camara borrosa negra enfoque lente '
           'permiso whatsapp',
  'aliases': ['camara negra', 'camera black', 'blurry', 'borrosa', 'no enfoca', 'whatsapp camera'],
  'text': 'Camera issues can be caused by lens dirt, app permissions, storage, app bugs, software, or a damaged camera '
          'module. Clean the lens gently, test another camera app, restart, and check camera permissions.'},
 {'id': 'network_sim_signal_apn',
  'category': 'network_issue',
  'risk': 'LOW',
  'topic': 'wifi sim network internet signal coverage no service emergency calls mobile data antenna apn sin servicio '
           'cobertura datos red señal antena llamadas',
  'aliases': ['no signal',
              'not have signals',
              'no service',
              'sin servicio',
              'sin cobertura',
              'emergency calls',
              'sim',
              'apn',
              'datos moviles'],
  'text': 'Network problems may be caused by SIM card failure, operator coverage, APN settings, airplane mode, '
          'software configuration, or antenna damage after a drop. Test the SIM in another phone if possible, toggle '
          'airplane mode, restart, and check mobile data/APN settings.'},
 {'id': 'software_storage_malware',
  'category': 'software_issue',
  'risk': 'LOW',
  'topic': 'apps slow storage update virus malware memory lag lento almacenamiento actualizacion se cierra bloquea '
           'anuncios popups',
  'aliases': ['lento', 'slow', 'storage full', 'se bloquea', 'apps crash', 'virus', 'malware', 'popups'],
  'text': 'Slow phones and app crashes are often related to low storage, outdated software, buggy apps, malware, or '
          'too many background processes. Free space, update apps, remove suspicious apps, and back up data before '
          'major resets.'},
 {'id': 'warranty_spain_consumer',
  'category': 'warranty',
  'risk': 'LOW',
  'topic': 'warranty guarantee repair receipt Spain invoice refund return garantia factura legal tienda segunda mano',
  'aliases': ['garantia', 'warranty', 'factura', 'invoice', 'refund', 'devolucion', 'segunda mano'],
  'text': 'In Spain, new consumer electronics sold from 1 January 2022 generally have a 3-year legal warranty. '
          'Second-hand goods can have a shorter agreed warranty, but it cannot be less than 1 year. Keep the receipt '
          'or invoice and check terms before opening or repairing the device.'},
 {'id': 'data_recovery_backup',
  'category': 'data_recovery',
  'risk': 'MEDIUM',
  'topic': 'data recovery photos backup whatsapp icloud google drive datos fotos recuperar copia seguridad pantalla '
           'rota no enciende',
  'aliases': ['recuperar datos', 'data recovery', 'photos', 'whatsapp', 'backup', 'copia seguridad'],
  'text': 'If the user needs photos, WhatsApp, contacts, or other important data, avoid factory reset until backup '
          'options are checked. For broken screens or boot issues, data recovery depends on device encryption, screen '
          'access, account credentials, and hardware condition.'},
 {'id': 'image_visual_inspection',
  'category': 'image_analysis',
  'risk': 'LOW',
  'topic': 'photo image screenshot scam sms damage battery screen visible evidence camera multimodal foto captura daño '
           'visible',
  'aliases': ['foto', 'image', 'screenshot', 'captura', 'visible damage'],
  'text': 'A photo or screenshot can help identify visible clues such as screen lifting, cracked glass, water marks, '
          'damaged ports, or phishing SMS characteristics. Only visible evidence should be mentioned; do not claim '
          'internal damage from an image alone.'},
 {'id': 'app_whatsapp_not_working',
  'category': 'app_issue',
  'risk': 'LOW',
  'topic': 'whatsapp whastapp watsapp whatsap wasap no funciona not working no abre se cierra crash cache update '
           'storage internet app',
  'aliases': ['whatsapp',
              'whastapp',
              'watsapp',
              'whatsap',
              'wasap',
              'whats app',
              'app no funciona',
              'se cierra',
              'no abre'],
  'text': 'WhatsApp/app issues are usually caused by corrupted cache, outdated app version, low storage, unstable '
          'internet, notification permission problems, or a temporary service outage. Safe checks: restart the phone, '
          'test WiFi and mobile data, update the app, check free storage, clear the app cache on Android, and '
          'reinstall only after confirming chats are backed up. Do not factory reset for a single app problem.'},
 {'id': 'app_social_media_login_crash',
  'category': 'app_issue',
  'risk': 'LOW',
  'topic': 'instagram tiktok facebook telegram youtube gmail app login crash force close loading not responding se '
           'cierra no inicia no carga',
  'aliases': ['instagram no funciona',
              'tiktok no funciona',
              'gmail no funciona',
              'youtube no funciona',
              'force close',
              'loading forever'],
  'text': 'When one app such as Instagram, TikTok, Facebook, Telegram, Gmail or YouTube fails, the cause is usually '
          'app cache, outdated app version, account/login issue, permissions, low storage, or a server outage. If only '
          'one app fails, it is usually not a motherboard or screen repair issue.'},
 {'id': 'online_service_outage_basic',
  'category': 'online_service_issue',
  'risk': 'LOW',
  'topic': 'server down service unavailable outage cannot connect login failed cloud server whatsapp instagram tiktok '
           'online issue',
  'aliases': ['server down',
              'caida',
              'caído',
              'servicio caido',
              'cannot connect',
              'service unavailable',
              'login failed'],
  'text': 'Some app problems are caused by a temporary online service outage. Check whether other apps work, try WiFi '
          'and mobile data, ask another person if the same app works, and wait before deleting data. A service outage '
          'does not require phone repair.'},
 {'id': 'wifi_connection_basic',
  'category': 'wifi_issue',
  'risk': 'LOW',
  'topic': 'wifi wi fi internet router dns cannot connect disconnecting slow no conecta contraseña red red wifi',
  'aliases': ['wifi no funciona', 'no conecta wifi', 'internet lento', 'wifi disconnecting', 'cannot connect wifi'],
  'text': 'WiFi problems can come from the router, saved password, DNS, network settings, VPN, software update, or the '
          'phone WiFi antenna. Safe checks: restart router and phone, forget the network and reconnect, test another '
          'WiFi, disable VPN, and compare with mobile data.'},
 {'id': 'bluetooth_pairing_basic',
  'category': 'bluetooth_issue',
  'risk': 'LOW',
  'topic': 'bluetooth airpods headphones speaker car not pairing disconnecting no conecta auriculares altavoz coche '
           'emparejar',
  'aliases': ['bluetooth no conecta', 'airpods no conecta', 'not pairing', 'se desconecta bluetooth'],
  'text': 'Bluetooth problems are often caused by old pairing data, low battery in the accessory, '
          'distance/interference, software bugs, or accessory incompatibility. Forget the device, restart both '
          'devices, test another accessory, and update the phone before assuming hardware damage.'},
 {'id': 'storage_full_app_system',
  'category': 'storage_issue',
  'risk': 'LOW',
  'topic': 'storage full memory full almacenamiento lleno espacio lleno cannot install apps whatsapp update low '
           'storage fotos videos',
  'aliases': ['almacenamiento lleno', 'espacio lleno', 'storage full', 'memory full', 'no puedo instalar'],
  'text': 'Low storage can make apps crash, WhatsApp fail, updates fail, camera stop saving photos, and the phone '
          'become slow. Free space by deleting large videos, clearing app cache, moving photos to cloud/PC, and '
          'keeping at least several GB free before updates.'},
 {'id': 'ios_android_update_failed',
  'category': 'update_issue',
  'risk': 'MEDIUM',
  'topic': 'ios android update failed stuck updating actualización fallida se queda actualizando boot after update '
           'software update',
  'aliases': ['update failed', 'actualización fallida', 'ios update', 'android update', 'stuck updating'],
  'text': 'Update failures can be caused by low storage, low battery, interrupted download, corrupted system files, or '
          'incompatible firmware. Do not factory reset if data matters. Charge the phone, connect stable WiFi, free '
          'storage, and use official recovery/update tools if needed.'},
 {'id': 'overheating_safety_shutdown',
  'category': 'overheating_issue',
  'risk': 'HIGH',
  'topic': 'overheating phone hot gets hot charging burning smell caliente sobrecalentado olor quemado se calienta '
           'mucho',
  'aliases': ['se calienta mucho', 'phone hot', 'overheating', 'burning smell', 'olor quemado'],
  'text': 'A phone that becomes very hot, smells burned, heats while charging, or shuts down from heat may have a '
          'battery, charging, short-circuit, or board issue. Stop charging, remove the case, keep it away from heat, '
          'and get professional inspection if heat is strong or repeated.'},
 {'id': 'faceid_touchid_biometric',
  'category': 'faceid_touchid_issue',
  'risk': 'MEDIUM',
  'topic': 'face id touch id fingerprint biometric face unlock huella reconocimiento facial no funciona',
  'aliases': ['face id no funciona', 'touch id no funciona', 'fingerprint not working', 'huella no funciona'],
  'text': 'Face ID/Touch ID/fingerprint issues can be caused by dirty sensors, screen protector, moisture, software '
          'update, camera/sensor damage, or previous repair. Clean the sensor area, remove problematic protector, '
          'restart, update, and re-enroll biometrics. After water or impact, professional diagnosis may be needed.'},
 {'id': 'charging_port_dirty_loose',
  'category': 'charging_port_issue',
  'risk': 'MEDIUM',
  'topic': 'charging port usb c lightning loose only charges angle dirty connector puerto carga flojo solo carga '
           'moviendo cable',
  'aliases': ['puerto de carga',
              'charging port',
              'solo carga moviendo',
              'charges at angle',
              'usb c flojo',
              'lightning flojo'],
  'text': 'A loose charging port or charging only at an angle often means lint/dirt in the port, worn connector, '
          'damaged cable, or port damage. Do not force the cable or insert metal tools. Test a known-good cable and '
          'charger; if still loose, professional cleaning or port repair is needed.'},
 {'id': 'camera_focus_lens_permission',
  'category': 'camera_issue',
  'risk': 'MEDIUM',
  'topic': 'camera blurry black focus shaking lens permission camera app camara borrosa negra enfoque vibra permiso '
           'lente',
  'aliases': ['camara borrosa', 'camera blurry', 'camera black', 'no enfoca', 'focus issue', 'camera shaking'],
  'text': 'Camera issues can come from dirty lens, broken lens glass, app permission, software crash, autofocus/OIS '
          'failure, or camera module damage. Clean lens with microfiber, test the default camera app, check '
          'permissions, restart, and compare front/back cameras.'},
 {'id': 'speaker_microphone_call_audio',
  'category': 'audio_issue',
  'risk': 'LOW',
  'topic': 'speaker microphone mic call audio no me escuchan no se escucha altavoz microfono llamadas auricular sonido '
           'bajo',
  'aliases': ['no me escuchan',
              'no se escucha',
              'speaker not working',
              'microphone not working',
              'altavoz',
              'microfono'],
  'text': 'Call audio issues can be caused by Bluetooth routing, blocked speaker/mic grille, dust, case cover, app '
          'permission, software bug, water damage, or damaged audio component. Disable Bluetooth, test voice recorder, '
          'test speaker mode, remove case, and avoid liquids in the grille.'},
 {'id': 'screen_lines_touch_oled',
  'category': 'screen_repair',
  'risk': 'MEDIUM',
  'topic': 'green line black screen touch not working flickering dead pixels oled lcd pantalla verde negra tactil '
           'lineas manchas',
  'aliases': ['green line', 'linea verde', 'pantalla negra', 'black screen', 'touch not working', 'tactil no funciona'],
  'text': 'Screen lines, black display, flickering, dead pixels, or touch failure may indicate OLED/LCD/display cable '
          'damage, impact damage, water damage, or software freeze. Back up data if possible and avoid pressing the '
          'screen. If the phone still vibrates/rings but image is black, display repair may be needed.'},
 {'id': 'privacy_before_repair',
  'category': 'privacy_repair',
  'risk': 'MEDIUM',
  'topic': 'privacy data before repair backup erase passcode photos whatsapp private data repair shop privacidad datos '
           'antes reparar',
  'aliases': ['privacidad', 'datos privados', 'before repair', 'antes de reparar', 'borrar datos'],
  'text': 'Before leaving a phone for repair, protect privacy: make a backup, remove sensitive apps if possible, sign '
          'out of accounts only when needed, and never share banking passwords. For diagnostics, technicians may need '
          'the passcode only if testing requires access; use repair mode if available.'},
 {'id': 'photo_visual_inspection_external',
  'category': 'image_analysis',
  'risk': 'LOW',
  'topic': 'photo image visual inspection screen crack battery swelling port corrosion water damage screenshot sms '
           'physical evidence',
  'aliases': ['foto', 'photo', 'image', 'screenshot', 'captura', 'imagen'],
  'text': 'When a customer sends a photo, only visible external evidence should be used: cracked glass, lifted screen, '
          'liquid warning, corrosion, bent frame, damaged port, burn marks, or suspicious SMS text. Do not guess '
          'hidden board damage from a photo alone. Ask for symptoms if the photo is unclear.'},
 {'id': 'photo_screen_crack_display',
  'category': 'screen_repair',
  'risk': 'MEDIUM',
  'topic': 'photo cracked screen broken glass green line black display oled lcd touch not working visible damage',
  'aliases': ['cracked screen', 'broken screen', 'pantalla rota', 'línea verde', 'green line', 'black display'],
  'text': 'From a photo, visible cracked glass, green lines, OLED/LCD stains, flickering, black display, or touch '
          'failure point to screen/display damage. Do not claim board damage unless there are other symptoms. '
          'Recommend backup if the screen still works.'},
 {'id': 'photo_battery_swelling_lifted_screen',
  'category': 'battery_safety',
  'risk': 'HIGH',
  'topic': 'photo swollen battery lifted screen back cover bulging battery safety risk',
  'aliases': ['swollen battery', 'lifted screen', 'screen lifting', 'batería hinchada', 'pantalla levantada'],
  'text': 'A lifted screen, bulging back cover, or visible gap can indicate a swollen battery. This is a high-risk '
          'safety case: stop charging, do not press the phone, and arrange professional battery replacement.'},
 {'id': 'photo_charging_port_damage',
  'category': 'charging_port_issue',
  'risk': 'MEDIUM',
  'topic': 'photo charging port usb c lightning dirty loose broken bent connector lint visible damage',
  'aliases': ['charging port', 'usb c', 'lightning port', 'puerto de carga', 'conector sucio'],
  'text': 'A photo of a charging port can reveal lint, dirt, bent pins, corrosion, broken plastic, or a loose '
          'connector. Avoid metal tools and forcing the cable. If multiple cables fail or the connector is loose, a '
          'technician should inspect it.'},
 {'id': 'photo_water_corrosion_visible',
  'category': 'water_damage',
  'risk': 'HIGH',
  'topic': 'photo visible corrosion liquid damage rust moisture warning salt water oxidation',
  'aliases': ['corrosion', 'oxidation', 'water damage', 'liquid damage', 'corrosión', 'óxido', 'humedad'],
  'text': 'Visible corrosion, liquid residue, rust, moisture warnings, or signs of salt water are high-risk. Do not '
          'charge the phone, do not use heat or rice, and get professional inspection quickly to reduce corrosion and '
          'data-loss risk.'},
 {'id': 'photo_scam_sms_screenshot',
  'category': 'scam_phishing',
  'risk': 'HIGH',
  'topic': 'screenshot sms bank link card otp password phishing scam suspicious message',
  'aliases': ['sms banco', 'bank sms', 'otp', 'tarjeta', 'card', 'link', 'phishing'],
  'text': 'If a screenshot shows a bank, delivery, tax, WhatsApp, or account message asking for card details, '
          'password, PIN, OTP code, or a suspicious link, treat it as phishing. Do not open links or enter '
          'credentials.'},
 {'id': 'photo_app_error_screenshot',
  'category': 'app_issue',
  'risk': 'LOW',
  'topic': 'screenshot app error whatsapp instagram tiktok login crash storage update cache not working',
  'aliases': ['app error', 'whatsapp error', 'instagram error', 'login failed', 'no funciona', 'se cierra'],
  'text': 'A screenshot of an app error usually points to app cache, outdated version, login/service outage, unstable '
          'internet, or low storage. Try restart, update, clear cache, check storage and network before repair.'},
 {'id': 'photo_camera_lens_damage',
  'category': 'camera_issue',
  'risk': 'MEDIUM',
  'topic': 'photo camera lens cracked scratched blurry focus black camera visible lens damage',
  'aliases': ['camera lens', 'lente cámara', 'camera glass', 'foto borrosa', 'focus problem'],
  'text': 'Visible cracked camera glass, dirt, scratches, condensation, or lens damage can cause blurry photos, focus '
          'problems, black camera, or flares. Clean gently first; if still blurry or cracked, a technician should '
          'inspect the camera glass/module.'},
 {'id': 'photo_unclear_quality',
  'category': 'image_analysis',
  'risk': 'LOW',
  'topic': 'unclear blurry dark low resolution image ask better photo no guessing',
  'aliases': ['blurry photo', 'dark photo', 'low resolution', 'foto borrosa', 'imagen oscura'],
  'text': 'If a photo is blurry, too dark, too bright, cropped, or too low-resolution, do not guess. Ask for a clearer '
          'photo from good light, close enough to the problem, plus a short text description of symptoms.'}]

CATEGORY_RESPONSE_TEMPLATES = {'English': {'charging_issue': {'diagnosis': 'the most likely causes are a faulty cable/charger, dirt inside the '
                                             'charging port, a damaged or loose charging port, software trouble, or a '
                                             'worn battery.',
                                'action': 'Try another certified cable and charger, restart the phone, and check if '
                                          'the cable feels loose. Do not force the cable and do not put metal objects '
                                          'inside the port.',
                                'visit': 'if it does not charge with several cables, the port is loose, the phone gets '
                                         'hot, there is moisture/liquid warning, or the battery percentage drops while '
                                         'charging.'},
             'charging_port_issue': {'diagnosis': 'the charging port may be dirty, loose, damaged, or not making '
                                                  'stable contact with the cable.',
                                     'action': 'Try a certified cable, test another charger, check whether the '
                                               'connector moves too much, and avoid forcing the cable.',
                                     'visit': 'if it only charges at an angle, disconnects often, shows moisture '
                                              'warning, or does not charge with multiple cables.'},
             'app_issue': {'diagnosis': 'the app may be failing because of corrupted cache, low storage, an outdated '
                                        'app version, internet problems, or a temporary service outage.',
                           'action': 'Restart the phone, check WiFi/mobile data, update the app, clear the app cache '
                                     'if available, and check free storage.',
                           'visit': 'if many apps fail, the phone freezes, the system is very slow, or the problem '
                                    'continues after updates and storage cleanup.'},
             'network_issue': {'diagnosis': 'it may be a SIM, mobile network, APN/settings, carrier coverage, '
                                            'software, or antenna-related issue.',
                               'action': 'Restart the phone, toggle airplane mode, test another SIM if possible, check '
                                         'mobile data/APN settings, and check if the issue happens in another area.',
                               'visit': 'if different SIM cards fail, the phone had a drop/water damage, or it always '
                                        'shows no service.'},
             'sim_network_issue': {'diagnosis': 'the issue may be related to the SIM card, SIM tray, carrier settings, '
                                                'mobile network coverage, APN configuration, or antenna circuit.',
                                   'action': 'Restart the phone, remove and reinsert the SIM, test another SIM, check '
                                             'carrier settings, and reset network settings if data is backed up.',
                                   'visit': 'if the phone never detects any SIM, shows emergency calls only, or the '
                                            'issue started after a drop or liquid damage.'},
             'water_damage': {'diagnosis': 'liquid may have entered the phone and can cause corrosion or short '
                                           'circuits, even if the phone still turns on.',
                              'action': 'Turn it off, do not charge it, do not use heat or rice, remove case/SIM tray '
                                        'if safe, and keep it dry.',
                              'visit': 'as soon as possible, especially after salt water, charging attempts, heat, '
                                       'screen issues, or important data risk.'},
             'battery_safety': {'diagnosis': 'the battery may be swollen or unsafe.',
                                'action': 'Stop using and charging the phone. Do not press the screen or puncture the '
                                          'battery.',
                                'visit': 'immediately. A swollen battery is a safety risk.'},
             'overheating_issue': {'diagnosis': 'the phone may be overheating due to battery stress, charging '
                                                'problems, heavy apps, liquid damage, or board-level issues.',
                                   'action': 'Stop charging, remove the case, close heavy apps, and let the phone cool '
                                             'down.',
                                   'visit': 'if it becomes very hot, smells burnt, shuts down, or heats up while '
                                            'charging.'},
             'screen_repair': {'diagnosis': 'the display, touch layer, connector, or screen assembly may be damaged.',
                               'action': 'Restart the phone and avoid pressing the screen. Back up data if the screen '
                                         'still works.',
                               'visit': 'if the screen is black, flickering, has lines, ghost touch, or touch does not '
                                        'respond.'},
             'camera_issue': {'diagnosis': 'the camera may have a software issue, dirty lens, focus problem, or '
                                           'damaged camera module.',
                              'action': 'Clean the lens gently, restart the phone, test another camera app, and check '
                                        'for updates.',
                              'visit': 'if the camera is black, blurry after cleaning, shaking, or the issue started '
                                       'after a drop/water damage.'},
             'speaker_microphone_issue': {'diagnosis': 'it may be caused by dirt in the speaker/microphone, Bluetooth '
                                                       'routing, app permissions, software, or a damaged audio '
                                                       'component.',
                                          'action': 'Turn off Bluetooth, test voice recorder, test a normal call and '
                                                    'speaker mode, and clean only the outside grille gently.',
                                          'visit': 'if calls remain unclear, the microphone records no sound, or the '
                                                   'issue started after water/dust.'},
             'wifi_issue': {'diagnosis': 'it may be a router, WiFi settings, software, DNS, or WiFi antenna issue.',
                            'action': 'Restart the phone and router, forget and reconnect the WiFi network, test '
                                      'another WiFi, and check if mobile data works.',
                            'visit': 'if all WiFi networks fail or the issue started after drop/water damage.'},
             'bluetooth_issue': {'diagnosis': 'it may be pairing trouble, Bluetooth cache/settings, accessory issue, '
                                              'or software problem.',
                                 'action': 'Forget the Bluetooth device, restart both devices, pair again, and test '
                                           'another accessory.',
                                 'visit': 'if no Bluetooth devices connect or the issue started after physical '
                                          'damage.'},
             'storage_issue': {'diagnosis': 'low storage can make apps crash, updates fail, photos stop saving, and '
                                            'the phone run slowly.',
                               'action': 'Delete unused apps/files, move photos to backup, clear app cache, and keep '
                                         'at least a few GB free.',
                               'visit': 'if the phone is stuck, cannot boot, or you need help recovering data.'},
             'update_issue': {'diagnosis': 'a failed or corrupted software update may cause freezing, boot loop, app '
                                           'crashes, or system errors.',
                              'action': 'Do not factory reset if you need data. Try forced restart and ensure enough '
                                        'battery/storage.',
                              'visit': 'if it is stuck on logo/update screen, restarts repeatedly, or contains '
                                       'important data.'},
             'boot_issue': {'diagnosis': 'it may be a failed update, corrupted system, low battery, storage problem, '
                                         'or board-level issue.',
                            'action': 'Try a forced restart and charge with a known good charger. Do not factory reset '
                                      'if data matters.',
                            'visit': 'if it stays on logo, restarts in a loop, does not turn on, or you need data '
                                     'recovery.'},
             'data_recovery': {'diagnosis': 'data may still be recoverable depending on the storage, screen, board, '
                                            'and previous reset/backup status.',
                               'action': 'Stop trying random resets. Do not erase the phone. Check '
                                         'iCloud/Google/WhatsApp backups first.',
                               'visit': 'if the phone does not boot, screen is broken, or the data is important.'},
             'scam_phishing': {'diagnosis': 'this looks like a possible phishing/scam attempt.',
                               'action': 'Do not open the link, do not enter card details or codes, block/report the '
                                         'sender, and contact your bank using the official app or phone number.',
                               'visit': 'if you already entered details, call the bank immediately and change '
                                        'passwords.'},
               'scam_clicked_link': {'diagnosis': 'you opened a phishing link — act immediately even if you did not enter any data.',
                               'action': '1) Close the browser now. 2) Clear browser history and cache. 3) Change bank and email passwords from a DIFFERENT device. 4) Enable 2-factor authentication on your bank app. 5) Monitor your bank accounts for 30 days.',
                               'visit': 'call your bank now and explain that you opened a suspicious link — they can flag your account.'},
             'privacy_repair': {'diagnosis': 'the repair may expose personal data if the phone is unlocked or handed '
                                             'over without precautions.',
                                'action': 'Back up your data, remove sensitive apps where possible, sign out of '
                                          'accounts if needed, and ask the technician what access is required.',
                                'visit': 'choose a trusted repair shop and avoid sharing passcodes unless strictly '
                                         'necessary.'},
             'vague_problem': {'diagnosis': 'there is not enough information yet to know whether the issue is screen, '
                                            'charging, battery, software, signal, audio, camera, or an app.',
                               'action': 'Tell me whether the phone turns on, charges, shows image, has signal, or if '
                                         'a specific app fails. Meanwhile, try a forced restart and basic charging '
                                         'test without forcing the connector.',
                               'visit': 'if it does not turn on, overheats, had water/drop damage, has a swollen '
                                        'battery, or contains important data.'},
             'unknown': {'diagnosis': 'there is no safe match with the information provided.',
                         'action': 'Describe the exact symptom: screen, charging, battery, signal/SIM, sound, camera, '
                                   'app, or data. Also mention drop, water, update, or recent repair.',
                         'visit': 'if the issue repeats, affects important data, started after water/drop, or the '
                                  'phone overheats.'},
             'photo_unclear': {'diagnosis': 'the photo is not clear enough to confirm the problem safely.',
                               'action': 'Send another photo with good light, focus, and close to the faulty area. '
                                         'Also write what happens: not charging, broken screen, app issue, water, '
                                         'signal, or audio.',
                               'visit': 'if there is battery swelling, water damage, heat, strange smell, lifted '
                                        'screen, or important data.'},
             'image_analysis': {'diagnosis': 'the photo is not clear enough to confirm the problem safely.',
                                'action': 'Send another photo with good light, focus, and close to the faulty area. '
                                          'Also write what happens: not charging, broken screen, app issue, water, '
                                          'signal, or audio.',
                                'visit': 'if there is battery swelling, water damage, heat, strange smell, lifted '
                                         'screen, or important data.'}},
 'Spanish': {'charging_issue': {'diagnosis': 'puede ser cable/cargador defectuoso, puerto de carga sucio o dañado, '
                                             'software o batería gastada.',
                                'action': 'Prueba otro cable y cargador certificado. No fuerces el cable ni metas '
                                          'objetos metálicos en el puerto.',
                                'visit': 'si no carga con varios cables, el puerto está flojo, hay calor, humedad o el '
                                         'porcentaje baja cargando.'},
             'charging_port_issue': {'diagnosis': 'el puerto de carga puede estar sucio, flojo, dañado o sin buen '
                                                  'contacto con el cable.',
                                     'action': 'Prueba cable certificado, otro cargador y mira si el conector se mueve '
                                               'demasiado. No fuerces el cable.',
                                     'visit': 'si solo carga en una posición, se desconecta, aparece humedad o no '
                                              'carga con varios cables.'},
             'app_issue': {'diagnosis': 'la app puede fallar por caché dañada, poco espacio, versión antigua, problema '
                                        'de internet o caída temporal del servicio.',
                           'action': 'Reinicia el móvil, comprueba WiFi/datos, actualiza la app, borra caché si se '
                                     'puede y revisa espacio libre.',
                           'visit': 'si fallan muchas apps, el móvil se congela, va muy lento o sigue igual tras '
                                    'actualizar y liberar espacio.'},
             'network_issue': {'diagnosis': 'puede ser problema de SIM, red móvil, APN/ajustes, cobertura del '
                                            'operador, software o antena.',
                               'action': 'Reinicia, activa/desactiva modo avión, prueba otra SIM si puedes, revisa '
                                         'APN/datos móviles y prueba en otra zona.',
                               'visit': 'si fallan varias SIM, hubo golpe/agua o siempre aparece sin servicio.'},
             'sim_network_issue': {'diagnosis': 'puede estar relacionado con SIM, bandeja SIM, ajustes del operador, '
                                                'cobertura, APN o antena.',
                                   'action': 'Reinicia, saca y vuelve a poner la SIM, prueba otra SIM, revisa ajustes '
                                             'del operador y restablece ajustes de red si tienes copia.',
                                   'visit': 'si no detecta ninguna SIM, solo sale emergencia o empezó tras '
                                            'golpe/agua.'},
             'water_damage': {'diagnosis': 'puede haber entrado líquido y causar corrosión o cortocircuito aunque el '
                                           'móvil aún encienda.',
                              'action': 'Apágalo, no lo cargues, no uses calor ni arroz, quita funda/SIM si es seguro '
                                        'y mantenlo seco.',
                              'visit': 'lo antes posible, sobre todo si fue agua salada, intentaste cargarlo, se '
                                       'calienta, falla pantalla o hay datos importantes.'},
             'battery_safety': {'diagnosis': 'la batería puede estar hinchada o ser insegura.',
                                'action': 'Deja de usarlo y cargarlo. No presiones la pantalla ni pinches la batería.',
                                'visit': 'inmediatamente. Una batería hinchada es riesgo de seguridad.'},
             'overheating_issue': {'diagnosis': 'puede calentarse por batería, carga, apps pesadas, líquido o problema '
                                                'de placa.',
                                   'action': 'Deja de cargarlo, quita la funda, cierra apps pesadas y deja que se '
                                             'enfríe.',
                                   'visit': 'si quema, huele raro, se apaga o se calienta al cargar.'},
             'screen_repair': {'diagnosis': 'puede estar dañado el display, táctil, conector o módulo de pantalla.',
                               'action': 'Reinicia y evita presionar la pantalla. Haz copia si aún puedes usarla.',
                               'visit': 'si está negra, parpadea, tiene líneas, toque fantasma o no responde.'},
             'camera_issue': {'diagnosis': 'puede ser software, lente sucia, enfoque o módulo de cámara dañado.',
                              'action': 'Limpia la lente suavemente, reinicia, prueba otra app de cámara y revisa '
                                        'actualizaciones.',
                              'visit': 'si sale negra, sigue borrosa, vibra o empezó tras golpe/agua.'},
             'speaker_microphone_issue': {'diagnosis': 'puede ser suciedad en altavoz/micrófono, Bluetooth, permisos, '
                                                       'software o pieza de audio dañada.',
                                          'action': 'Apaga Bluetooth, prueba grabadora de voz, llamada normal y '
                                                    'altavoz, y limpia solo por fuera con cuidado.',
                                          'visit': 'si las llamadas siguen mal, el micro no graba o empezó tras '
                                                   'agua/polvo.'},
             'wifi_issue': {'diagnosis': 'puede ser router, ajustes WiFi, software, DNS o antena WiFi.',
                            'action': 'Reinicia móvil y router, olvida y reconecta la red, prueba otro WiFi y mira si '
                                      'funcionan los datos móviles.',
                            'visit': 'si fallan todas las redes WiFi o empezó tras golpe/agua.'},
             'bluetooth_issue': {'diagnosis': 'puede ser emparejamiento, caché/ajustes Bluetooth, accesorio o '
                                              'software.',
                                 'action': 'Olvida el dispositivo, reinicia ambos, vuelve a emparejar y prueba otro '
                                           'accesorio.',
                                 'visit': 'si no conecta ningún Bluetooth o empezó tras daño físico.'},
             'storage_issue': {'diagnosis': 'poco almacenamiento puede cerrar apps, fallar actualizaciones, impedir '
                                            'guardar fotos y ralentizar el móvil.',
                               'action': 'Borra apps/archivos que no uses, pasa fotos a copia, limpia caché y deja '
                                         'varios GB libres.',
                               'visit': 'si está bloqueado, no arranca o necesitas recuperar datos.'},
             'update_issue': {'diagnosis': 'una actualización fallida o corrupta puede causar bloqueos, bootloop, '
                                           'fallos de apps o errores del sistema.',
                              'action': 'No hagas reset si necesitas datos. Prueba reinicio forzado y asegúrate de '
                                        'tener batería/espacio.',
                              'visit': 'si se queda en logo/actualización, se reinicia en bucle o hay datos '
                                       'importantes.'},
             'boot_issue': {'diagnosis': 'puede ser actualización fallida, sistema corrupto, batería baja, '
                                         'almacenamiento o placa.',
                            'action': 'Prueba reinicio forzado y carga con cargador bueno. No hagas reset si necesitas '
                                      'datos.',
                            'visit': 'si se queda en logo, se reinicia, no enciende o necesitas recuperar datos.'},
             'data_recovery': {'diagnosis': 'los datos podrían recuperarse según almacenamiento, pantalla, placa y si '
                                            'hubo reset/copia.',
                               'action': 'No hagas resets al azar. No borres el móvil. Revisa copias de '
                                         'iCloud/Google/WhatsApp.',
                               'visit': 'si no arranca, la pantalla está rota o los datos son importantes.'},
             'scam_phishing': {'diagnosis': 'parece un posible intento de phishing/estafa.',
                               'action': 'No abras el enlace, no pongas tarjeta ni códigos, bloquea/reportar el '
                                         'remitente y contacta con tu banco desde app o número oficial.',
                               'visit': 'si ya metiste datos, llama al banco inmediatamente y cambia contraseñas.'},
               'scam_clicked_link': {'diagnosis': 'has abierto un enlace de phishing — actúa ahora aunque no hayas puesto datos.' if 'Spanish' == 'Spanish' else 'you opened a phishing link — act now even if you did not enter data.',
                               'action': '1) Cierra el navegador. 2) Borra caché. 3) Cambia contraseñas desde otro dispositivo. 4) Activa 2FA en tu banco. 5) Supervisa movimientos 30 días.' if 'Spanish' == 'Spanish' else '1) Close the browser. 2) Clear cache. 3) Change passwords from a different device. 4) Enable 2FA on bank. 5) Monitor accounts 30 days.',
                               'visit': 'llama al banco ahora — explícales que abriste un enlace sospechoso.' if 'Spanish' == 'Spanish' else 'call your bank now — tell them you opened a suspicious link.'},
               'scam_data_entered': {'diagnosis': '¡EMERGENCIA! Has introducido tus datos en un sitio de phishing.',
                               'action': '1) LLAMA A TU BANCO AHORA — pide bloquear la tarjeta y cuenta. '
                                         '2) Cambia contraseñas del banco y email desde OTRO dispositivo. '
                                         '3) Activa 2FA en todos tus servicios. '
                                         '4) Denuncia en la Policía o Guardia Civil (formulario online). '
                                         '5) Guarda capturas del SMS como prueba.',
                               'visit': 'llama al banco INMEDIATAMENTE — cada minuto cuenta. '
                                        'Después ve a la Policía a presentar denuncia.'},
             'privacy_repair': {'diagnosis': 'la reparación puede exponer datos personales si entregas el móvil '
                                             'desbloqueado o sin precauciones.',
                                'action': 'Haz copia, elimina apps sensibles si puedes, cierra sesiones si hace falta '
                                          'y pregunta qué acceso necesita el técnico.',
                                'visit': 'elige una tienda de confianza y no compartas contraseña salvo que sea '
                                         'imprescindible.'},
             'vague_problem': {'diagnosis': 'todavía no hay suficiente información para saber si es pantalla, carga, '
                                            'batería, software, señal, sonido, cámara o una app.',
                               'action': 'Dime si enciende, carga, muestra imagen, tiene señal o si falla una app '
                                         'concreta. Mientras tanto, prueba reinicio forzado y carga básica sin forzar '
                                         'el conector.',
                               'visit': 'si no enciende, se calienta, hubo agua/golpe, la batería está hinchada o '
                                        'tienes datos importantes.'},
             'unknown': {'diagnosis': 'no hay una coincidencia segura con la información actual.',
                         'action': 'Explica el síntoma exacto: pantalla, carga, batería, señal/SIM, sonido, cámara, '
                                   'app o datos. Indica si hubo golpe, agua, actualización o reparación previa.',
                         'visit': 'si se repite, afecta a datos importantes, empezó tras agua/golpe o el móvil se '
                                  'calienta.'},
             'photo_unclear': {'diagnosis': 'la foto no permite confirmar el problema con seguridad.',
                               'action': 'Envía otra foto con buena luz, enfocada y cerca de la zona del fallo. Añade '
                                         'también qué pasa: no carga, pantalla rota, app falla, agua, señal o sonido.',
                               'visit': 'si hay batería hinchada, agua, calor, olor raro, pantalla levantada o datos '
                                        'importantes.'},
             'image_analysis': {'diagnosis': 'la foto no permite confirmar el problema con seguridad.',
                                'action': 'Envía otra foto con buena luz, enfocada y cerca de la zona del fallo. Añade '
                                          'también qué pasa: no carga, pantalla rota, app falla, agua, señal o sonido.',
                                'visit': 'si hay batería hinchada, agua, calor, olor raro, pantalla levantada o datos '
                                         'importantes.'}},
 'Catalan': {'charging_issue': {'diagnosis': 'les causes més probables són un cable o carregador defectuós, brutícia '
                                             'al port de càrrega, port malmès o bateria gastada.',
                                'action': 'Prova un altre cable i carregador certificat, reinicia el mòbil i comprova '
                                          'si el connector queda fluix. No forcis el cable ni posis objectes '
                                          'metàl·lics dins del port.',
                                'visit': "si no carrega amb diversos cables, el port està fluix, el mòbil s'escalfa, "
                                         "hi ha avís d'humitat o el percentatge baixa mentre carrega."},
             'charging_port_issue': {'diagnosis': 'el port de càrrega pot estar brut, fluix, malmès o sense bon '
                                                  'contacte amb el cable.',
                                     'action': 'Prova un cable certificat, un altre carregador i mira si el connector '
                                               'es mou massa. No forcis el cable.',
                                     'visit': 'si només carrega en una posició, es desconnecta sovint, apareix humitat '
                                              'o no carrega amb diversos cables.'},
             'app_issue': {'diagnosis': "l'app pot fallar per memòria cau danyada, poc espai lliure, versió antiga, "
                                        "problema d'internet o caiguda temporal del servei.",
                           'action': "Reinicia el mòbil, comprova WiFi/dades mòbils, actualitza l'app, esborra la "
                                     "memòria cau si es pot i revisa l'espai lliure.",
                           'visit': 'si fallen moltes apps, el mòbil es congela, va molt lent o continua igual després '
                                    "d'actualitzar i alliberar espai."},
             'network_issue': {'diagnosis': 'pot ser un problema de SIM, xarxa mòbil, APN/configuració, cobertura de '
                                            "l'operador, software o antena.",
                               'action': 'Reinicia, activa/desactiva mode avió, prova una altra SIM si pots, revisa '
                                         'APN/dades mòbils i prova en una altra zona.',
                               'visit': 'si fallen diverses SIM, hi va haver cop/aigua o sempre surt sense servei.'},
             'sim_network_issue': {'diagnosis': 'pot estar relacionat amb la SIM, safata SIM, configuració de '
                                                "l'operador, cobertura, APN o antena.",
                                   'action': 'Reinicia, treu i torna a posar la SIM, prova una altra SIM, revisa la '
                                             "configuració de l'operador i restableix ajustos de xarxa si tens còpia.",
                                   'visit': "si no detecta cap SIM, només mostra trucades d'emergència o va començar "
                                            "després d'un cop o aigua."},
             'water_damage': {'diagnosis': 'pot haver entrat líquid i causar corrosió o curtcircuit encara que el '
                                           "mòbil encara s'encengui.",
                              'action': "Apaga'l, no el carreguis, no facis servir calor ni arròs, treu funda/SIM si "
                                        'és segur i mantén-lo sec.',
                              'visit': "com més aviat millor, sobretot si era aigua salada, s'ha intentat carregar, "
                                       "s'escalfa, falla la pantalla o hi ha dades importants."},
             'battery_safety': {'diagnosis': 'la bateria pot estar inflada o ser insegura.',
                                'action': "Deixa d'utilitzar-lo i de carregar-lo. No pressionis la pantalla ni punxis "
                                          'la bateria.',
                                'visit': 'immediatament. Una bateria inflada és un risc de seguretat.'},
             'overheating_issue': {'diagnosis': 'el mòbil pot escalfar-se per bateria, càrrega, apps pesades, líquid o '
                                                'problema de placa.',
                                   'action': 'Deixa de carregar-lo, treu la funda, tanca apps pesades i deixa que es '
                                             'refredi.',
                                   'visit': "si crema, fa olor estranya, s'apaga o s'escalfa mentre carrega."},
             'screen_repair': {'diagnosis': 'pot estar danyat el display, el tàctil, el connector o el mòdul de '
                                            'pantalla.',
                               'action': 'Reinicia i evita pressionar la pantalla. Fes còpia si encara la pots '
                                         'utilitzar.',
                               'visit': 'si la pantalla és negra, parpelleja, té línies, toc fantasma o no respon.'},
             'camera_issue': {'diagnosis': "pot ser software, lent bruta, problema d'enfocament o mòdul de càmera "
                                           'danyat.',
                              'action': 'Neteja la lent suaument, reinicia, prova una altra app de càmera i revisa '
                                        'actualitzacions.',
                              'visit': "si surt negra, continua borrosa, vibra o va començar després d'un cop o "
                                       'aigua.'},
             'speaker_microphone_issue': {'diagnosis': "pot ser brutícia a l'altaveu/micròfon, Bluetooth, permisos, "
                                                       "software o peça d'àudio danyada.",
                                          'action': 'Apaga Bluetooth, prova gravadora de veu, trucada normal i mode '
                                                    'altaveu, i neteja només per fora amb cura.',
                                          'visit': 'si les trucades continuen malament, el micròfon no grava o va '
                                                   "començar després d'aigua/pols."},
             'wifi_issue': {'diagnosis': 'pot ser router, ajustos WiFi, software, DNS o antena WiFi.',
                            'action': 'Reinicia mòbil i router, oblida i reconnecta la xarxa, prova un altre WiFi i '
                                      'mira si funcionen les dades mòbils.',
                            'visit': "si fallen totes les xarxes WiFi o va començar després d'un cop/aigua."},
             'bluetooth_issue': {'diagnosis': 'pot ser emparellament, caché/ajustos Bluetooth, accessori o software.',
                                 'action': 'Oblida el dispositiu Bluetooth, reinicia tots dos, torna a emparellar i '
                                           'prova un altre accessori.',
                                 'visit': 'si no connecta cap dispositiu Bluetooth o va començar després de dany '
                                          'físic.'},
             'storage_issue': {'diagnosis': 'poc espai pot tancar apps, fer fallar actualitzacions, impedir guardar '
                                            'fotos i alentir el mòbil.',
                               'action': 'Esborra apps/arxius que no utilitzis, passa fotos a còpia, neteja caché i '
                                         'deixa diversos GB lliures.',
                               'visit': 'si està bloquejat, no arrenca o necessites recuperar dades.'},
             'update_issue': {'diagnosis': 'una actualització fallida o corrupta pot causar bloquejos, reinicis, '
                                           "errors d'apps o problemes del sistema.",
                              'action': 'No facis reset si necessites dades. Prova reinici forçat i assegura '
                                        'bateria/espai suficient.',
                              'visit': 'si queda al logo/actualització, es reinicia en bucle o hi ha dades '
                                       'importants.'},
             'boot_issue': {'diagnosis': 'pot ser una actualització fallida, sistema corrupte, bateria baixa, '
                                         'emmagatzematge o placa.',
                            'action': 'Prova reinici forçat i càrrega amb carregador fiable. No facis reset si '
                                      'necessites dades.',
                            'visit': "si queda al logo, es reinicia, no s'encén o necessites recuperar dades."},
             'data_recovery': {'diagnosis': "les dades podrien recuperar-se segons l'emmagatzematge, pantalla, placa i "
                                            'si hi ha reset o còpia.',
                               'action': "No facis resets a l'atzar. No esborris el mòbil. Revisa còpies "
                                         "d'iCloud/Google/WhatsApp.",
                               'visit': 'si no arrenca, la pantalla està trencada o les dades són importants.'},
             'scam_phishing': {'diagnosis': 'sembla un possible intent de phishing o estafa.',
                               'action': "No obris l'enllaç, no posis targeta ni codis, bloqueja/reportar el remitent "
                                         "i contacta amb el banc des de l'app o número oficial.",
                               'visit': 'si ja has posat dades, truca al banc immediatament i canvia contrasenyes.'},
               'scam_clicked_link': {'diagnosis': 'has obert un enllaç de phishing — actua ara encara que no hagis introduït dades.',
                               'action': "1) Tanca el navegador ara. 2) Esborra l'historial i la memòria cau. 3) Canvia contrasenyes del banc i correu des d'UN ALTRE dispositiu. 4) Activa la verificació en 2 passos al banc. 5) Supervisa els moviments 30 dies.",
                               'visit': "truca al banc ara — explica'ls que has obert un enllaç sospitós."},
             'privacy_repair': {'diagnosis': 'la reparació pot exposar dades personals si entregues el mòbil '
                                             'desbloquejat o sense precaucions.',
                                'action': 'Fes còpia, elimina apps sensibles si pots, tanca sessions si cal i pregunta '
                                          'quin accés necessita el tècnic.',
                                'visit': 'tria una botiga de confiança i no comparteixis contrasenya si no és '
                                         'imprescindible.'},
             'vague_problem': {'diagnosis': 'encara no hi ha prou informació per saber si és pantalla, càrrega, '
                                            'bateria, software, senyal, so, càmera o una app.',
                               'action': "Digues-me si s'encén, carrega, mostra imatge, té senyal o si falla una app "
                                         'concreta. Mentrestant, prova reinici forçat i càrrega bàsica sense forçar el '
                                         'connector.',
                               'visit': "si no s'encén, s'escalfa, hi va haver aigua/cop, la bateria està inflada o "
                                        'tens dades importants.'},
             'unknown': {'diagnosis': 'no hi ha una coincidència segura amb la informació actual.',
                         'action': 'Explica el símptoma exacte: pantalla, càrrega, bateria, senyal/SIM, so, càmera, '
                                   'app o dades. Indica si hi va haver cop, aigua, actualització o reparació prèvia.',
                         'visit': "si es repeteix, afecta dades importants, va començar després d'aigua/cop o el mòbil "
                                  "s'escalfa."},
             'photo_unclear': {'diagnosis': 'la foto no és prou clara per confirmar el problema amb seguretat.',
                               'action': 'Envia una altra foto amb bona llum, enfocada i prop de la zona del problema. '
                                         'Afegeix també què passa: no carrega, pantalla trencada, app falla, aigua, '
                                         'senyal o so.',
                               'visit': 'si hi ha bateria inflada, aigua, calor, olor estranya, pantalla aixecada o '
                                        'dades importants.'},
             'image_analysis': {'diagnosis': 'la foto no és prou clara per confirmar el problema amb seguretat.',
                                'action': 'Envia una altra foto amb bona llum, enfocada i prop de la zona del '
                                          'problema. Afegeix també què passa: no carrega, pantalla trencada, app '
                                          'falla, aigua, senyal o so.',
                                'visit': 'si hi ha bateria inflada, aigua, calor, olor estranya, pantalla aixecada o '
                                         'dades importants.'}},
 'Urdu': {'charging_issue': {'diagnosis': 'ممکن ہے مسئلہ خراب کیبل/چارجر، چارجنگ پورٹ میں مٹی، خراب پورٹ، سافٹ ویئر یا '
                                          'پرانی بیٹری کی وجہ سے ہو۔',
                             'action': 'دوسری اصل یا معیاری کیبل اور چارجر سے چیک کریں، فون ری اسٹارٹ کریں، اور کیبل '
                                       'کو زبردستی نہ لگائیں۔ پورٹ میں دھاتی چیز نہ ڈالیں۔',
                             'visit': 'اگر کئی کیبلز سے بھی چارج نہ ہو، پورٹ ڈھیلا ہو، فون گرم ہو، نمی کا پیغام آئے یا '
                                      'چارج کم ہوتا رہے۔'},
          'charging_port_issue': {'diagnosis': 'چارجنگ پورٹ گندی، ڈھیلی، خراب یا کیبل کے ساتھ صحیح رابطہ نہیں بنا رہی '
                                               'ہو سکتی ہے۔',
                                  'action': 'معیاری کیبل اور دوسرا چارجر آزما کر دیکھیں، کنیکٹر زیادہ ہلتا ہے یا نہیں '
                                            'دیکھیں، اور کیبل زبردستی نہ لگائیں۔',
                                  'visit': 'اگر صرف ایک خاص زاویے پر چارج ہو، بار بار ڈسکنیکٹ ہو، نمی کا پیغام آئے یا '
                                           'کئی کیبلز سے بھی چارج نہ ہو۔'},
          'app_issue': {'diagnosis': 'ایپ خراب کیش، کم اسٹوریج، پرانے ورژن، انٹرنیٹ مسئلے یا عارضی سروس ڈاؤن ہونے کی '
                                     'وجہ سے نہیں چل رہی ہو سکتی۔',
                        'action': 'فون ری اسٹارٹ کریں، WiFi/موبائل ڈیٹا چیک کریں، ایپ اپڈیٹ کریں، کیش صاف کریں اگر '
                                  'ممکن ہو، اور خالی اسٹوریج چیک کریں۔',
                        'visit': 'اگر کئی ایپس بند ہو رہی ہیں، فون فریز ہوتا ہے، بہت سست ہے یا اپڈیٹ اور اسٹوریج صاف '
                                 'کرنے کے بعد بھی مسئلہ رہے۔'},
          'network_issue': {'diagnosis': 'مسئلہ SIM، موبائل نیٹ ورک، APN/سیٹنگز، آپریٹر کوریج، سافٹ ویئر یا اینٹینا سے '
                                         'ہو سکتا ہے۔',
                            'action': 'فون ری اسٹارٹ کریں، ایئرپلین موڈ آن/آف کریں، ممکن ہو تو دوسری SIM لگائیں، '
                                      'APN/موبائل ڈیٹا چیک کریں اور دوسری جگہ پر ٹیسٹ کریں۔',
                            'visit': 'اگر مختلف SIM بھی کام نہ کریں، فون کو جھٹکا/پانی لگا ہو یا ہمیشہ No Service '
                                     'دکھائے۔'},
          'sim_network_issue': {'diagnosis': 'یہ SIM کارڈ، SIM ٹرے، آپریٹر سیٹنگز، کوریج، APN یا اینٹینا کا مسئلہ ہو '
                                             'سکتا ہے۔',
                                'action': 'فون ری اسٹارٹ کریں، SIM نکال کر دوبارہ لگائیں، دوسری SIM ٹیسٹ کریں، نیٹ ورک '
                                          'سیٹنگز چیک کریں اور بیک اپ کے بعد نیٹ ورک ری سیٹ کریں۔',
                                'visit': 'اگر فون کوئی SIM نہ پہچانے، صرف Emergency Calls دکھائے یا مسئلہ گرنے/پانی کے '
                                         'بعد شروع ہوا ہو۔'},
          'water_damage': {'diagnosis': 'فون میں پانی/نمی داخل ہو سکتی ہے جس سے corrosion یا short circuit ہو سکتا ہے، '
                                        'چاہے فون ابھی آن ہو۔',
                           'action': 'فون بند کریں، چارج نہ کریں، heat یا rice استعمال نہ کریں، کیس/SIM ٹرے اگر محفوظ '
                                     'ہو تو نکالیں اور خشک جگہ رکھیں۔',
                           'visit': 'جلد از جلد، خاص طور پر اگر نمکین پانی لگا، چارج کرنے کی کوشش کی، فون گرم ہے، '
                                    'screen خراب ہے یا اہم ڈیٹا ہے۔'},
          'battery_safety': {'diagnosis': 'بیٹری پھولی ہوئی یا unsafe ہو سکتی ہے۔',
                             'action': 'فون استعمال اور چارج کرنا بند کریں۔ screen کو دبائیں نہیں اور بیٹری کو '
                                       'puncture نہ کریں۔',
                             'visit': 'فوراً۔ پھولی ہوئی بیٹری safety risk ہے۔'},
          'overheating_issue': {'diagnosis': 'فون battery stress، charging issue، heavy apps، liquid damage یا board '
                                             'issue کی وجہ سے گرم ہو سکتا ہے۔',
                                'action': 'چارجنگ روک دیں، cover اتاریں، heavy apps بند کریں اور فون کو ٹھنڈا ہونے '
                                          'دیں۔',
                                'visit': 'اگر بہت زیادہ گرم ہو، جلنے جیسی بو آئے، خود بند ہو یا charging پر گرم ہو۔'},
          'screen_repair': {'diagnosis': 'display، touch layer، connector یا screen module خراب ہو سکتا ہے۔',
                            'action': 'فون ری اسٹارٹ کریں اور screen پر دباؤ نہ ڈالیں۔ اگر screen چل رہی ہے تو data '
                                      'backup کر لیں۔',
                            'visit': 'اگر screen black ہے، flicker کرتی ہے، lines ہیں، ghost touch ہے یا touch کام '
                                     'نہیں کرتا۔'},
          'camera_issue': {'diagnosis': 'مسئلہ software، lens dirty، focus problem یا camera module damage ہو سکتا ہے۔',
                           'action': 'lens نرمی سے صاف کریں، فون ری اسٹارٹ کریں، دوسری camera app آزما کر دیکھیں اور '
                                     'update چیک کریں۔',
                           'visit': 'اگر camera black ہے، cleaning کے بعد بھی blurry ہے، shake کرتا ہے یا drop/water '
                                    'کے بعد issue شروع ہوا۔'},
          'speaker_microphone_issue': {'diagnosis': 'speaker/microphone میں مٹی، Bluetooth routing، app permissions، '
                                                    'software یا audio part damage ہو سکتا ہے۔',
                                       'action': 'Bluetooth بند کریں، voice recorder ٹیسٹ کریں، normal call اور '
                                                 'speaker mode چیک کریں، grille کو باہر سے احتیاط سے صاف کریں۔',
                                       'visit': 'اگر calls اب بھی clear نہیں، microphone record نہیں کرتا یا مسئلہ '
                                                'water/dust کے بعد شروع ہوا۔'},
          'wifi_issue': {'diagnosis': 'مسئلہ router، WiFi settings، software، DNS یا WiFi antenna سے ہو سکتا ہے۔',
                         'action': 'فون اور router ری اسٹارٹ کریں، WiFi network بھلا کر دوبارہ connect کریں، دوسری '
                                   'WiFi ٹیسٹ کریں اور mobile data چیک کریں۔',
                         'visit': 'اگر تمام WiFi networks fail ہوں یا مسئلہ drop/water کے بعد شروع ہوا۔'},
          'bluetooth_issue': {'diagnosis': 'pairing، Bluetooth settings/cache، accessory یا software کا مسئلہ ہو سکتا '
                                           'ہے۔',
                              'action': 'Bluetooth device forget کریں، دونوں devices ری اسٹارٹ کریں، دوبارہ pair کریں '
                                        'اور دوسرا accessory ٹیسٹ کریں۔',
                              'visit': 'اگر کوئی بھی Bluetooth device connect نہ ہو یا مسئلہ physical damage کے بعد '
                                       'شروع ہوا۔'},
          'storage_issue': {'diagnosis': 'کم storage کی وجہ سے apps بند ہو سکتی ہیں، updates fail ہو سکتے ہیں، photos '
                                         'save نہیں ہوتیں اور phone slow ہو سکتا ہے۔',
                            'action': 'غیر ضروری apps/files delete کریں، photos backup کریں، cache صاف کریں اور کچھ GB '
                                      'space خالی رکھیں۔',
                            'visit': 'اگر فون stuck ہے، boot نہیں ہوتا یا data recover کرنا ہے۔'},
          'update_issue': {'diagnosis': 'failed یا corrupted software update کی وجہ سے freezing، boot loop، app '
                                        'crashes یا system errors ہو سکتے ہیں۔',
                           'action': 'اگر data چاہیے تو factory reset نہ کریں۔ forced restart کریں اور battery/storage '
                                     'کافی رکھیں۔',
                           'visit': 'اگر logo/update screen پر stuck ہے، بار بار restart ہوتا ہے یا important data '
                                    'ہے۔'},
          'boot_issue': {'diagnosis': 'failed update، corrupted system، low battery، storage issue یا board-level '
                                      'issue ہو سکتا ہے۔',
                         'action': 'forced restart کریں اور اچھے charger سے charge کریں۔ اگر data important ہے تو '
                                   'reset نہ کریں۔',
                         'visit': 'اگر logo پر stuck ہے، restart loop ہے، on نہیں ہوتا یا data recovery چاہیے۔'},
          'data_recovery': {'diagnosis': 'data recover ہو سکتا ہے یا نہیں، یہ storage، screen، board اور reset/backup '
                                         'status پر depend کرتا ہے۔',
                            'action': 'random reset نہ کریں۔ فون erase نہ کریں۔ iCloud/Google/WhatsApp backup پہلے '
                                      'check کریں۔',
                            'visit': 'اگر phone boot نہیں ہوتا، screen ٹوٹ گئی ہے یا data important ہے۔'},
          'scam_phishing': {'diagnosis': 'یہ phishing/scam لگ رہا ہے۔',
                            'action': 'link نہ کھولیں، card details یا codes نہ دیں، sender block/report کریں اور bank '
                                      'کو official app یا number سے contact کریں۔',
                            'visit': 'اگر آپ details ڈال چکے ہیں تو فوراً bank کو call کریں اور passwords change '
                                     'کریں۔'},
               'scam_clicked_link': {'diagnosis': 'آپ نے فشنگ لنک کھولا — فوری کارروائی کریں چاہے ڈیٹا نہ دیا ہو۔',
                               'action': 'براؤزر بند کریں۔ ہسٹری اور کیشے صاف کریں۔ دوسرے ڈیوائس سے بینک اور ایمیل پاسورڈ بدلیں۔ 2FA آن کریں۔ 30 دن تک اکاؤنٹ مانیٹر کریں۔',
                               'visit': 'ابھی بینک کو کال کریں — بتائیں کہ مشکوک لنک کھولا تھا۔'},
          'privacy_repair': {'diagnosis': 'repair کے دوران personal data expose ہو سکتا ہے اگر phone unlocked یا بغیر '
                                          'احتیاط کے دیا جائے۔',
                             'action': 'backup بنائیں، sensitive apps remove/sign out کریں اگر possible ہو، اور '
                                       'technician سے پوچھیں کہ access کیوں چاہیے۔',
                             'visit': 'trusted repair shop choose کریں اور password صرف ضرورت ہو تو دیں۔'},
          'vague_problem': {'diagnosis': 'ابھی اتنی معلومات نہیں کہ معلوم ہو مسئلہ screen، charging، battery، '
                                         'software، signal، sound، camera یا app کا ہے۔',
                            'action': 'بتائیں phone on ہوتا ہے؟ charge لیتا ہے؟ screen image دکھاتی ہے؟ signal ہے؟ یا '
                                      'کوئی specific app fail ہے؟ فی الحال forced restart اور basic charging test کریں '
                                      'مگر connector کو force نہ کریں۔',
                            'visit': 'اگر phone on نہیں ہوتا، گرم ہوتا ہے، water/drop damage ہوا ہے، battery swollen '
                                     'ہے یا important data ہے۔'},
          'unknown': {'diagnosis': 'موجودہ معلومات سے محفوظ اور clear match نہیں مل رہا۔',
                      'action': 'exact symptom بتائیں: screen، charging، battery، signal/SIM، sound، camera، app یا '
                                'data۔ یہ بھی بتائیں کہ drop، water، update یا previous repair ہوا تھا یا نہیں۔',
                      'visit': 'اگر مسئلہ repeat ہو، important data affect ہو، water/drop کے بعد شروع ہوا ہو یا phone '
                               'گرم ہو۔'},
          'photo_unclear': {'diagnosis': 'تصویر اتنی واضح نہیں کہ مسئلہ محفوظ طریقے سے confirm کیا جا سکے۔',
                            'action': 'اچھی روشنی میں واضح اور قریب سے دوبارہ تصویر بھیجیں، اور ساتھ لکھیں مسئلہ کیا '
                                      'ہے: charge نہیں ہوتا، screen ٹوٹی ہے، app fail ہے، water، signal یا audio '
                                      'issue۔',
                            'visit': 'اگر battery swollen ہے، water damage، heat، عجیب smell، screen lifted ہے یا '
                                     'important data ہے۔'},
          'image_analysis': {'diagnosis': 'تصویر اتنی واضح نہیں کہ مسئلہ محفوظ طریقے سے confirm کیا جا سکے۔',
                             'action': 'اچھی روشنی میں واضح اور قریب سے دوبارہ تصویر بھیجیں، اور ساتھ لکھیں مسئلہ کیا '
                                       'ہے: charge نہیں ہوتا، screen ٹوٹی ہے، app fail ہے، water، signal یا audio '
                                       'issue۔',
                             'visit': 'اگر battery swollen ہے، water damage، heat، عجیب smell، screen lifted ہے یا '
                                      'important data ہے۔'}},
 'Arabic': {'charging_issue': {'diagnosis': 'قد يكون السبب كابل أو شاحن تالف، اتساخ منفذ الشحن، تلف المنفذ، مشكلة '
                                            'برمجية أو بطارية مستهلكة.',
                               'action': 'جرّب كابل وشاحن معتمدين آخرين، أعد تشغيل الهاتف، وتأكد هل الكابل غير ثابت. '
                                         'لا تضغط الكابل ولا تدخل أدوات معدنية في المنفذ.',
                               'visit': 'إذا لم يشحن بعدة كابلات، أو كان المنفذ مرتخياً، أو الهاتف يسخن، أو ظهرت '
                                        'رطوبة، أو تنخفض النسبة أثناء الشحن.'},
            'charging_port_issue': {'diagnosis': 'منفذ الشحن قد يكون متسخاً، مرتخياً، تالفاً أو لا يلامس الكابل بشكل '
                                                 'جيد.',
                                    'action': 'جرّب كابل معتمد وشاحناً آخر، وافحص هل يتحرك الموصل كثيراً. لا تضغط '
                                              'الكابل بقوة.',
                                    'visit': 'إذا كان يشحن فقط بزاوية معينة، أو يفصل كثيراً، أو يظهر تحذير رطوبة، أو '
                                             'لا يشحن بعدة كابلات.'},
            'app_issue': {'diagnosis': 'قد لا يعمل التطبيق بسبب كاش تالف، نقص مساحة، إصدار قديم، مشكلة إنترنت أو توقف '
                                       'مؤقت في الخدمة.',
                          'action': 'أعد تشغيل الهاتف، افحص WiFi/بيانات الهاتف، حدّث التطبيق، امسح الكاش إن أمكن، '
                                    'وتأكد من وجود مساحة فارغة.',
                          'visit': 'إذا تعطلت عدة تطبيقات، أو الهاتف يتجمد، أو بطيء جداً، أو يستمر العطل بعد التحديث '
                                   'وتحرير المساحة.'},
            'network_issue': {'diagnosis': 'قد تكون المشكلة في الشريحة SIM، الشبكة، إعدادات APN، تغطية المشغل، '
                                           'البرمجيات أو الهوائي.',
                              'action': 'أعد التشغيل، فعّل/أوقف وضع الطيران، جرّب شريحة أخرى إن أمكن، راجع إعدادات APN '
                                        'والبيانات، وجرب في مكان آخر.',
                              'visit': 'إذا فشلت عدة شرائح، أو حدث سقوط/ماء، أو يظهر دائماً No Service.'},
            'sim_network_issue': {'diagnosis': 'قد تكون المشكلة في الشريحة، درج الشريحة، إعدادات المشغل، التغطية، APN '
                                               'أو الهوائي.',
                                  'action': 'أعد تشغيل الهاتف، أخرج الشريحة وأعد إدخالها، جرّب شريحة أخرى، راجع '
                                            'إعدادات المشغل وأعد ضبط الشبكة بعد النسخ الاحتياطي.',
                                  'visit': 'إذا لم يتعرف على أي شريحة، أو يظهر طوارئ فقط، أو بدأ بعد سقوط/ماء.'},
            'water_damage': {'diagnosis': 'قد يكون دخل سائل للهاتف ويسبب تآكلاً أو قصر دائرة حتى لو كان الهاتف يعمل.',
                             'action': 'أطفئ الهاتف، لا تشحنه، لا تستخدم حرارة أو أرز، أزل الجراب/درج SIM إذا كان '
                                       'آمناً، واتركه جافاً.',
                             'visit': 'في أقرب وقت، خاصة إذا كان ماءً مالحاً، أو حاولت شحنه، أو يسخن، أو الشاشة تتعطل، '
                                      'أو توجد بيانات مهمة.'},
            'battery_safety': {'diagnosis': 'قد تكون البطارية منتفخة أو غير آمنة.',
                               'action': 'توقف عن استخدام الهاتف وشحنه. لا تضغط الشاشة ولا تثقب البطارية.',
                               'visit': 'فوراً. البطارية المنتفخة خطر أمان.'},
            'overheating_issue': {'diagnosis': 'قد يسخن الهاتف بسبب البطارية، الشحن، التطبيقات الثقيلة، ضرر سائل أو '
                                               'مشكلة في اللوحة.',
                                  'action': 'أوقف الشحن، انزع الجراب، أغلق التطبيقات الثقيلة واترك الهاتف يبرد.',
                                  'visit': 'إذا أصبح شديد السخونة، ظهرت رائحة احتراق، انطفأ، أو يسخن أثناء الشحن.'},
            'screen_repair': {'diagnosis': 'قد يكون التلف في الشاشة، اللمس، الموصل أو وحدة الشاشة.',
                              'action': 'أعد التشغيل وتجنب الضغط على الشاشة. انسخ بياناتك إذا كانت الشاشة ما زالت '
                                        'تعمل.',
                              'visit': 'إذا كانت الشاشة سوداء، تومض، بها خطوط، لمس عشوائي أو لا تستجيب.'},
            'camera_issue': {'diagnosis': 'قد يكون السبب برمجياً، عدسة متسخة، مشكلة تركيز أو تلف وحدة الكاميرا.',
                             'action': 'نظف العدسة بلطف، أعد التشغيل، جرّب تطبيق كاميرا آخر وتحقق من التحديثات.',
                             'visit': 'إذا كانت الكاميرا سوداء، أو ما زالت ضبابية، أو تهتز، أو بدأ بعد سقوط/ماء.'},
            'speaker_microphone_issue': {'diagnosis': 'قد يكون السبب اتساخ السماعة/الميكروفون، Bluetooth، الصلاحيات، '
                                                      'البرمجيات أو تلف قطعة صوت.',
                                         'action': 'أوقف Bluetooth، جرّب تسجيل صوت، مكالمة عادية ووضع مكبر الصوت، ونظف '
                                                   'الشبكة الخارجية فقط بلطف.',
                                         'visit': 'إذا بقيت المكالمات غير واضحة، أو الميكروفون لا يسجل، أو بدأ بعد '
                                                  'ماء/غبار.'},
            'wifi_issue': {'diagnosis': 'قد تكون المشكلة في الراوتر، إعدادات WiFi، البرمجيات، DNS أو هوائي WiFi.',
                           'action': 'أعد تشغيل الهاتف والراوتر، انسَ الشبكة وأعد الاتصال، جرّب WiFi آخر وتأكد هل '
                                     'بيانات الهاتف تعمل.',
                           'visit': 'إذا فشلت كل شبكات WiFi أو بدأ بعد سقوط/ماء.'},
            'bluetooth_issue': {'diagnosis': 'قد تكون مشكلة اقتران، إعدادات/كاش Bluetooth، الإكسسوار أو البرمجيات.',
                                'action': 'انسَ الجهاز، أعد تشغيل الجهازين، أعد الاقتران، وجرب إكسسواراً آخر.',
                                'visit': 'إذا لم يتصل بأي جهاز Bluetooth أو بدأ بعد ضرر مادي.'},
            'storage_issue': {'diagnosis': 'نقص المساحة قد يسبب إغلاق التطبيقات، فشل التحديثات، عدم حفظ الصور وبطء '
                                           'الهاتف.',
                              'action': 'احذف التطبيقات/الملفات غير الضرورية، انسخ الصور احتياطياً، امسح الكاش واترك '
                                        'عدة GB فارغة.',
                              'visit': 'إذا كان الهاتف عالقاً، لا يقلع، أو تحتاج استرجاع بيانات.'},
            'update_issue': {'diagnosis': 'تحديث فاشل أو تالف قد يسبب تجمد، إعادة تشغيل متكررة، تعطل تطبيقات أو أخطاء '
                                          'نظام.',
                             'action': 'لا تعمل فورمات إذا تحتاج البيانات. جرّب إعادة تشغيل قسرية وتأكد من البطارية '
                                       'والمساحة.',
                             'visit': 'إذا علق على الشعار/التحديث، يعيد التشغيل باستمرار أو توجد بيانات مهمة.'},
            'boot_issue': {'diagnosis': 'قد يكون السبب تحديثاً فاشلاً، نظاماً تالفاً، بطارية منخفضة، مشكلة تخزين أو '
                                        'لوحة.',
                           'action': 'جرّب إعادة تشغيل قسرية واشحن بشاحن موثوق. لا تعمل فورمات إذا تحتاج البيانات.',
                           'visit': 'إذا علق على الشعار، يعيد التشغيل، لا يشتغل أو تحتاج استرجاع بيانات.'},
            'data_recovery': {'diagnosis': 'قد تكون البيانات قابلة للاسترجاع حسب التخزين، الشاشة، اللوحة وهل تم '
                                           'الفورمات أو يوجد نسخ احتياطي.',
                              'action': 'لا تجرب فورمات عشوائي. لا تمسح الهاتف. افحص نسخ iCloud/Google/WhatsApp أولاً.',
                              'visit': 'إذا لا يقلع الهاتف، الشاشة مكسورة أو البيانات مهمة.'},
            'scam_phishing': {'diagnosis': 'يبدو أنه احتمال تصيد/احتيال.',
                              'action': 'لا تفتح الرابط، لا تدخل بيانات البطاقة أو الأكواد، احظر/بلّغ المرسل واتصل '
                                        'بالبنك من التطبيق أو الرقم الرسمي.',
                              'visit': 'إذا أدخلت بياناتك بالفعل، اتصل بالبنك فوراً وغيّر كلمات المرور.'},
               'scam_clicked_link': {'diagnosis': 'فتحت رابط تصيد — تصرف فوراً حتى لو لم تُدخل أي بيانات.',
                               'action': 'اغلق المتصفح الآن. امسح السجل ومخبأ المتصفح. غيّر كلمات مرور البنك والبريد من جهاز آخر. فعّل التحقق بخطوتين. راقب حسابك 30 يوماً.',
                               'visit': 'اتصل بالبنك الآن وأخبرهم أنك فتحت رابطاً مشبوهاً.'},
            'privacy_repair': {'diagnosis': 'قد يكشف الإصلاح بيانات شخصية إذا سلّمت الهاتف مفتوحاً أو دون احتياطات.',
                               'action': 'اعمل نسخة احتياطية، احذف التطبيقات الحساسة إن أمكن، سجّل الخروج إذا لزم، '
                                         'واسأل الفني لماذا يحتاج الوصول.',
                               'visit': 'اختر محل إصلاح موثوقاً ولا تشارك كلمة المرور إلا عند الضرورة.'},
            'vague_problem': {'diagnosis': 'لا توجد معلومات كافية لمعرفة هل المشكلة شاشة، شحن، بطارية، نظام، شبكة، '
                                           'صوت، كاميرا أو تطبيق.',
                              'action': 'أخبرني هل الهاتف يشتغل، يشحن، يعرض صورة، لديه شبكة، أو هل تطبيق معين لا يعمل. '
                                        'حالياً جرّب إعادة تشغيل قسرية واختبار شحن بسيط دون ضغط على المنفذ.',
                              'visit': 'إذا لا يشتغل، يسخن، تعرض لماء/سقوط، البطارية منتفخة أو توجد بيانات مهمة.'},
            'unknown': {'diagnosis': 'لا يوجد تطابق آمن وواضح بالمعلومات الحالية.',
                        'action': 'اشرح العرض بدقة: شاشة، شحن، بطارية، شبكة/SIM، صوت، كاميرا، تطبيق أو بيانات. واذكر '
                                  'هل حدث سقوط، ماء، تحديث أو إصلاح سابق.',
                        'visit': 'إذا يتكرر، يؤثر على بيانات مهمة، بدأ بعد ماء/سقوط أو الهاتف يسخن.'},
            'photo_unclear': {'diagnosis': 'الصورة غير واضحة بما يكفي لتأكيد المشكلة بأمان.',
                              'action': 'أرسل صورة أخرى بإضاءة جيدة وتركيز واضح وقريبة من مكان العطل. اكتب أيضاً ما '
                                        'يحدث: لا يشحن، شاشة مكسورة، تطبيق لا يعمل، ماء، شبكة أو صوت.',
                              'visit': 'إذا توجد بطارية منتفخة، ماء، حرارة، رائحة غريبة، شاشة مرفوعة أو بيانات مهمة.'},
            'image_analysis': {'diagnosis': 'الصورة غير واضحة بما يكفي لتأكيد المشكلة بأمان.',
                               'action': 'أرسل صورة أخرى بإضاءة جيدة وتركيز واضح وقريبة من مكان العطل. اكتب أيضاً ما '
                                         'يحدث: لا يشحن، شاشة مكسورة، تطبيق لا يعمل، ماء، شبكة أو صوت.',
                               'visit': 'إذا توجد بطارية منتفخة، ماء، حرارة، رائحة غريبة، شاشة مرفوعة أو بيانات '
                                        'مهمة.'}},
 'Romanian': {'charging_issue': {'diagnosis': 'cele mai probabile cauze sunt un cablu/încărcător defect, murdărie în '
                                              'portul de încărcare, port deteriorat, problemă software sau baterie '
                                              'uzată.',
                                 'action': 'Încearcă alt cablu și încărcător certificat, repornește telefonul și '
                                           'verifică dacă mufa stă slăbită. Nu forța cablul și nu introduce obiecte '
                                           'metalice în port.',
                                 'visit': 'dacă nu se încarcă cu mai multe cabluri, portul este slăbit, telefonul se '
                                          'încălzește, apare avertizare de umezeală sau procentul scade la încărcare.'},
              'charging_port_issue': {'diagnosis': 'portul de încărcare poate fi murdar, slăbit, deteriorat sau nu '
                                                   'face contact stabil cu cablul.',
                                      'action': 'Încearcă un cablu certificat, alt încărcător și verifică dacă mufa se '
                                                'mișcă prea mult. Nu forța cablul.',
                                      'visit': 'dacă se încarcă doar într-un anumit unghi, se deconectează des, apare '
                                               'umezeală sau nu se încarcă cu mai multe cabluri.'},
              'app_issue': {'diagnosis': 'aplicația poate eșua din cauza cache-ului corupt, spațiului redus, versiunii '
                                         'vechi, internetului sau unei căderi temporare a serviciului.',
                            'action': 'Repornește telefonul, verifică WiFi/datele mobile, actualizează aplicația, '
                                      'șterge cache-ul dacă se poate și verifică spațiul liber.',
                            'visit': 'dacă mai multe aplicații eșuează, telefonul îngheață, merge foarte lent sau '
                                     'problema continuă după update și eliberare de spațiu.'},
              'network_issue': {'diagnosis': 'poate fi o problemă cu SIM-ul, rețeaua mobilă, APN/setări, acoperirea '
                                             'operatorului, software-ul sau antena.',
                                'action': 'Repornește, activează/dezactivează modul avion, testează alt SIM dacă poți, '
                                          'verifică APN/date mobile și încearcă în altă zonă.',
                                'visit': 'dacă mai multe SIM-uri nu merg, a fost lovit/udat sau apare mereu fără '
                                         'semnal.'},
              'sim_network_issue': {'diagnosis': 'poate fi legat de cartela SIM, tava SIM, setările operatorului, '
                                                 'acoperire, APN sau antenă.',
                                    'action': 'Repornește telefonul, scoate și pune SIM-ul la loc, testează alt SIM, '
                                              'verifică setările operatorului și resetează setările de rețea după '
                                              'backup.',
                                    'visit': 'dacă nu detectează niciun SIM, apare doar apeluri de urgență sau a '
                                             'început după lovitură/apă.'},
              'water_damage': {'diagnosis': 'lichidul poate fi intrat în telefon și poate provoca coroziune sau '
                                            'scurtcircuit, chiar dacă telefonul pornește.',
                               'action': 'Oprește-l, nu îl încărca, nu folosi căldură sau orez, scoate husa/SIM dacă e '
                                         'sigur și păstrează-l uscat.',
                               'visit': 'cât mai repede, mai ales dacă a fost apă sărată, ai încercat să îl încarci, '
                                        'se încălzește, ecranul dă erori sau ai date importante.'},
              'battery_safety': {'diagnosis': 'bateria poate fi umflată sau nesigură.',
                                 'action': 'Oprește utilizarea și încărcarea. Nu apăsa ecranul și nu înțepa bateria.',
                                 'visit': 'imediat. O baterie umflată este risc de siguranță.'},
              'overheating_issue': {'diagnosis': 'telefonul se poate încălzi din cauza bateriei, încărcării, '
                                                 'aplicațiilor grele, lichidului sau unei probleme pe placă.',
                                    'action': 'Oprește încărcarea, scoate husa, închide aplicațiile grele și lasă '
                                              'telefonul să se răcească.',
                                    'visit': 'dacă devine foarte fierbinte, miroase ars, se oprește sau se încălzește '
                                             'la încărcare.'},
              'screen_repair': {'diagnosis': 'poate fi deteriorat display-ul, touch-ul, conectorul sau modulul de '
                                             'ecran.',
                                'action': 'Repornește și evită să apeși ecranul. Fă backup dacă încă îl poți folosi.',
                                'visit': 'dacă ecranul este negru, pâlpâie, are linii, ghost touch sau nu răspunde.'},
              'camera_issue': {'diagnosis': 'poate fi software, lentilă murdară, problemă de focus sau modul cameră '
                                            'deteriorat.',
                               'action': 'Curăță lentila ușor, repornește, testează altă aplicație de cameră și '
                                         'verifică update-uri.',
                               'visit': 'dacă imaginea este neagră, rămâne neclară, vibrează sau a început după '
                                        'lovitură/apă.'},
              'speaker_microphone_issue': {'diagnosis': 'poate fi murdărie în difuzor/microfon, Bluetooth, permisiuni, '
                                                        'software sau componentă audio defectă.',
                                           'action': 'Oprește Bluetooth, testează recorderul vocal, apel normal și '
                                                     'speaker, și curăță doar exteriorul grilei cu grijă.',
                                           'visit': 'dacă apelurile rămân neclare, microfonul nu înregistrează sau '
                                                    'problema a început după apă/praf.'},
              'wifi_issue': {'diagnosis': 'poate fi routerul, setările WiFi, software-ul, DNS-ul sau antena WiFi.',
                             'action': 'Repornește telefonul și routerul, uită și reconectează rețeaua, testează alt '
                                       'WiFi și verifică dacă datele mobile merg.',
                             'visit': 'dacă toate rețelele WiFi eșuează sau problema a început după lovitură/apă.'},
              'bluetooth_issue': {'diagnosis': 'poate fi o problemă de împerechere, cache/setări Bluetooth, accesoriu '
                                               'sau software.',
                                  'action': 'Uitá dispozitivul Bluetooth, repornește ambele dispozitive, împerechează '
                                            'din nou și testează alt accesoriu.',
                                  'visit': 'dacă nu se conectează la niciun dispozitiv Bluetooth sau a început după '
                                           'deteriorare fizică.'},
              'storage_issue': {'diagnosis': 'spațiul redus poate închide aplicații, bloca update-uri, opri salvarea '
                                             'pozelor și încetini telefonul.',
                                'action': 'Șterge aplicații/fișiere inutile, fă backup la poze, curăță cache-ul și '
                                          'lasă câțiva GB liberi.',
                                'visit': 'dacă telefonul este blocat, nu pornește sau ai nevoie de recuperare de '
                                         'date.'},
              'update_issue': {'diagnosis': 'un update eșuat sau corupt poate cauza blocări, bootloop, crash-uri de '
                                            'aplicații sau erori de sistem.',
                               'action': 'Nu face reset dacă ai nevoie de date. Încearcă restart forțat și asigură '
                                         'baterie/spațiu suficient.',
                               'visit': 'dacă rămâne la logo/update, se restartează în buclă sau ai date importante.'},
              'boot_issue': {'diagnosis': 'poate fi update eșuat, sistem corupt, baterie descărcată, problemă de '
                                          'stocare sau placă.',
                             'action': 'Încearcă restart forțat și încarcă cu un încărcător bun. Nu face reset dacă '
                                       'datele contează.',
                             'visit': 'dacă rămâne la logo, se restartează, nu pornește sau ai nevoie de recuperare '
                                      'date.'},
              'data_recovery': {'diagnosis': 'datele pot fi recuperabile în funcție de stocare, ecran, placă și dacă '
                                             's-a făcut reset/backup.',
                                'action': 'Nu face reseturi la întâmplare. Nu șterge telefonul. Verifică backup '
                                          'iCloud/Google/WhatsApp.',
                                'visit': 'dacă nu pornește, ecranul este spart sau datele sunt importante.'},
              'scam_phishing': {'diagnosis': 'pare o posibilă tentativă de phishing/înșelătorie.',
                                'action': 'Nu deschide linkul, nu introduce cardul sau coduri, blochează/raportează '
                                          'expeditorul și contactează banca prin aplicația sau numărul oficial.',
                                'visit': 'dacă ai introdus deja date, sună imediat banca și schimbă parolele.'},
               'scam_clicked_link': {'diagnosis': 'ai deschis un link de phishing — acționează imediat chiar dacă nu ai introdus date.',
                               'action': '1) Închide browserul acum. 2) Șterge istoricul și cache-ul. 3) Schimbă parolele băncii și emailului de pe UN ALT dispozitiv. 4) Activează autentificarea în 2 pași. 5) Monitorizează contul 30 de zile.',
                               'visit': 'sună banca acum și explică-le că ai deschis un link suspect.'},
              'privacy_repair': {'diagnosis': 'reparația poate expune date personale dacă predai telefonul deblocat '
                                              'sau fără precauții.',
                                 'action': 'Fă backup, elimină aplicații sensibile dacă poți, deloghează conturi dacă '
                                           'e nevoie și întreabă tehnicianul ce acces necesită.',
                                 'visit': 'alege un service de încredere și nu partaja parola decât dacă este strict '
                                          'necesar.'},
              'vague_problem': {'diagnosis': 'nu există încă suficiente informații ca să știm dacă problema este '
                                             'ecran, încărcare, baterie, software, semnal, sunet, cameră sau '
                                             'aplicație.',
                                'action': 'Spune dacă pornește, se încarcă, arată imagine, are semnal sau dacă o '
                                          'anumită aplicație nu merge. Între timp, încearcă restart forțat și test '
                                          'simplu de încărcare fără să forțezi portul.',
                                'visit': 'dacă nu pornește, se încălzește, a fost apă/lovitură, bateria este umflată '
                                         'sau ai date importante.'},
              'unknown': {'diagnosis': 'nu există o potrivire sigură cu informația actuală.',
                          'action': 'Descrie simptomul exact: ecran, încărcare, baterie, semnal/SIM, sunet, cameră, '
                                    'aplicație sau date. Spune și dacă a fost lovitură, apă, update sau reparație '
                                    'anterioară.',
                          'visit': 'dacă se repetă, afectează date importante, a început după apă/lovitură sau '
                                   'telefonul se încălzește.'},
              'photo_unclear': {'diagnosis': 'poza nu este suficient de clară pentru a confirma problema în siguranță.',
                                'action': 'Trimite altă poză cu lumină bună, focalizată și aproape de zona defectă. '
                                          'Spune și ce se întâmplă: nu încarcă, ecran spart, aplicație, apă, semnal '
                                          'sau audio.',
                                'visit': 'dacă există baterie umflată, apă, căldură, miros ciudat, ecran ridicat sau '
                                         'date importante.'},
              'image_analysis': {'diagnosis': 'poza nu este suficient de clară pentru a confirma problema în '
                                              'siguranță.',
                                 'action': 'Trimite altă poză cu lumină bună, focalizată și aproape de zona defectă. '
                                           'Spune și ce se întâmplă: nu încarcă, ecran spart, aplicație, apă, semnal '
                                           'sau audio.',
                                 'visit': 'dacă există baterie umflată, apă, căldură, miros ciudat, ecran ridicat sau '
                                          'date importante.'}}}

LABELS = {'Spanish': ['Diagnóstico probable',
             'Nivel de riesgo',
             'Qué hacer ahora',
             'Cuándo visitar a un profesional',
             'Fuentes usadas'],
 'English': ['Probable diagnosis', 'Risk level', 'What to do now', 'When to visit a technician', 'Sources used'],
 'Catalan': ['Diagnòstic probable',
             'Nivell de risc',
             'Què fer ara',
             'Quan visitar un professional',
             'Fonts utilitzades'],
 'Arabic': ['التشخيص المحتمل', 'مستوى الخطر', 'ماذا تفعل الآن', 'متى تزور فنيًا', 'المصادر المستخدمة'],
 'Romanian': ['Diagnostic probabil',
              'Nivel de risc',
              'Ce poți face acum',
              'Când să mergi la un tehnician',
              'Surse folosite'],
 'Urdu': ['ممکنہ تشخیص', 'خطرے کی سطح', 'اب کیا کریں', 'کب ٹیکنیشن کے پاس جائیں', 'استعمال شدہ ذرائع']}



# ── Additional scam/phishing knowledge docs ──────────────────────────────────
LOCAL_KNOWLEDGE.extend([
    {
        "id": "scam_sms_urgency_patterns",
        "category": "scam_phishing",
        "risk": "HIGH",
        "text": (
            "Smishing (SMS phishing) uses urgency tactics: account suspended, verify now, "
            "click within 24 hours. Real banks NEVER ask for PIN, card number, OTP or password "
            "via SMS or links. Forward suspicious messages to 7726 (SPAM) in Spain/UK. "
            "Report to INCIBE at incibe.es or call 017."
        ),
        "source": "INCIBE 2024 Smishing Guide",
        "languages": ["Spanish", "English", "Catalan", "Arabic", "Romanian", "Urdu"],
    },
    {
        "id": "scam_bizum_social_engineering",
        "category": "scam_phishing",
        "risk": "HIGH",
        "text": (
            "Bizum scams: fraudsters send money requests disguised as payments, "
            "or claim you won a prize. Never accept Bizum from unknowns. "
            "Fake CaixaBank, BBVA, Santander SMS are the most common in Spain. "
            "If you sent money to a scammer, call your bank immediately to block and reverse."
        ),
        "source": "Banco de España 2024",
        "languages": ["Spanish", "Catalan"],
    },
    {
        "id": "scam_phishing_url_check",
        "category": "scam_phishing",
        "risk": "HIGH",
        "text": (
            "How to spot a phishing URL: real bank domains end in .es or .com with the bank name. "
            "Fake URLs use: bank-secure.xyz, verify-account.tk, login-bbva.net. "
            "Check: hover over the link before clicking. If URL looks wrong, do not click. "
            "Install Google Safe Browsing or Norton Safe Web to auto-detect phishing."
        ),
        "source": "CERT Spain 2024",
        "languages": ["Spanish", "English", "Catalan", "Arabic", "Romanian", "Urdu"],
    },
])

# ── Aliases for compatibility ─────────────────────────────────────────────────
# SECTION_LABELS is the same as LABELS
SECTION_LABELS = LABELS

# ── PHOTO_VISUAL_CATEGORIES ───────────────────────────────────────────────────
# Maps visual damage patterns detected in photos to repair categories
PHOTO_VISUAL_CATEGORIES = {
    "swollen_battery": {
        "keywords": ["swollen", "bulging", "inflated", "lifted screen", "bent back"],
        "repair_category": "battery_safety",
        "urgency": "HIGH",
    },
    "cracked_screen": {
        "keywords": ["crack", "broken screen", "shattered", "lines on screen", "black spots"],
        "repair_category": "screen_repair",
        "urgency": "MEDIUM",
    },
    "water_damage": {
        "keywords": ["water", "wet", "liquid", "corrosion", "rust", "moisture"],
        "repair_category": "water_damage",
        "urgency": "HIGH",
    },
    "phishing_sms": {
        "keywords": ["sms", "text message", "bank", "link", "verify", "pin", "password"],
        "repair_category": "scam_phishing",
        "urgency": "HIGH",
    },
    "charging_port": {
        "keywords": ["port", "connector", "charging", "usb", "dirty port"],
        "repair_category": "charging_issue",
        "urgency": "MEDIUM",
    },
    "overheating": {
        "keywords": ["hot", "overheating", "burn marks", "discoloration"],
        "repair_category": "overheating_issue",
        "urgency": "HIGH",
    },
    "general_damage": {
        "keywords": ["damage", "broken", "physical damage"],
        "repair_category": "unknown",
        "urgency": "LOW",
    },
}

# ── REPAIRWISE_VERSION ────────────────────────────────────────────────────────
REPAIRWISE_VERSION = "V17"

# ── Extended knowledge base — added for hackathon v2 ────────────────────────
LOCAL_KNOWLEDGE.extend([
    # Charging
    {
        "id": "wireless_charging_issues",
        "category": "charging_issue",
        "risk": "LOW",
        "text": (
            "Wireless charging issues: dirty coil, thick case blocking contact, "
            "phone overheating during wireless charge (normal up to 40°C). "
            "Fix: remove case, clean back glass, use certified Qi charger. "
            "If wired charges but wireless does not: coil may be damaged, needs repair."
        ),
        "source": "RepairWise KB 2024",
        "languages": ["Spanish", "English", "Catalan", "Arabic", "Romanian", "Urdu"],
    },
    # Screen
    {
        "id": "screen_burn_in_oled",
        "category": "screen_repair",
        "risk": "LOW",
        "text": (
            "OLED screen burn-in: permanent ghost image from static content displayed too long. "
            "Prevention: auto-brightness on, dark mode, vary screen content. "
            "Partial fix: run pixel refresher tool if available in settings. "
            "Full fix: screen replacement. Common on Samsung AMOLED after 3+ years."
        ),
        "source": "RepairWise KB 2024",
        "languages": ["Spanish", "English"],
    },
    # Boot
    {
        "id": "boot_fastboot_recovery",
        "category": "boot_issue",
        "risk": "MEDIUM",
        "text": (
            "Phone stuck in fastboot or recovery mode: hold power + volume up/down to exit. "
            "If Android logo with red exclamation: tap power + volume up to enter recovery, "
            "select 'Reboot system now'. "
            "Factory reset only as last resort — backs up data first if possible. "
            "Caused by: failed OTA update, corrupted system partition, third-party ROM."
        ),
        "source": "RepairWise KB 2024",
        "languages": ["Spanish", "English", "Catalan"],
    },
    # Audio
    {
        "id": "audio_bluetooth_routing",
        "category": "audio_issue",
        "risk": "LOW",
        "text": (
            "No sound from speaker but Bluetooth connected: audio routing to BT device. "
            "Fix: disconnect Bluetooth or toggle off. "
            "Speaker quiet after water exposure: dry speaker grille with soft toothbrush, "
            "use speaker cleaner app (plays high-frequency tones to expel water). "
            "Never insert objects into speaker grille."
        ),
        "source": "RepairWise KB 2024",
        "languages": ["Spanish", "English", "Catalan", "Romanian"],
    },
    # Privacy
    {
        "id": "privacy_data_wipe_before_repair",
        "category": "privacy_repair",
        "risk": "MEDIUM",
        "text": (
            "Before handing phone to repair shop: back up data to Google/iCloud/local PC. "
            "Enable screen lock with PIN. Disable biometrics temporarily. "
            "Log out of banking and payment apps. Remove SIM and memory card. "
            "Use guest mode if available. Ask technician what access they need. "
            "Reputable shops should not need your unlock PIN for hardware repairs."
        ),
        "source": "INCIBE Privacy Guide 2024",
        "languages": ["Spanish", "English", "Catalan", "Arabic", "Romanian", "Urdu"],
    },
    # Battery drain
    {
        "id": "battery_drain_background_apps",
        "category": "battery_drain",
        "risk": "LOW",
        "text": (
            "Battery draining fast: check Settings > Battery for top consumers. "
            "Common culprits: location always-on, background refresh, push email, "
            "high screen brightness, 5G constant search in weak signal areas. "
            "Fix: restrict background for unused apps, use adaptive brightness, "
            "switch to WiFi calling in poor signal areas. "
            "Replace battery if capacity below 80% (check in Settings > Battery Health on iOS, "
            "or AccuBattery on Android)."
        ),
        "source": "RepairWise KB 2024",
        "languages": ["Spanish", "English", "Catalan", "Arabic", "Romanian", "Urdu"],
    },
    # Scam — new patterns
    {
        "id": "scam_delivery_parcel",
        "category": "scam_phishing",
        "risk": "HIGH",
        "text": (
            "Parcel delivery scams (Correos, DHL, FedEx impersonation): "
            "SMS says package held, pay customs fee via link. "
            "Real delivery companies NEVER ask for payment via SMS link. "
            "Check tracking only at official website directly. "
            "Common in Spain: fake Correos, fake Amazon delivery SMS. "
            "If clicked: report to INCIBE (017) and your bank immediately."
        ),
        "source": "INCIBE 2024",
        "languages": ["Spanish", "English", "Catalan"],
    },
    # Overheating
    {
        "id": "overheating_gaming_performance",
        "category": "overheating_issue",
        "risk": "LOW",
        "text": (
            "Phone overheating during gaming or video: normal up to 40-45°C. "
            "Dangerous above 50°C. Signs: throttling (games slow down), warning popup. "
            "Fix: lower graphics settings, take breaks, remove case during gaming, "
            "avoid direct sunlight, close background apps. "
            "Persistent overheating at normal use: check for malware or faulty battery."
        ),
        "source": "RepairWise KB 2024",
        "languages": ["Spanish", "English"],
    },
])

