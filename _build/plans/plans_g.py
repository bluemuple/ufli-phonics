# Getting Ready lessons A-J (sound wall + alphabet knowledge & letter formation)
P = {}
def gr(title, tag, sounds, sound_intro, letters, strokes, notes=None):
    return dict(gr=True, title=title, tag=tag, notes=notes or [], soundwall=dict(intro=sound_intro, sounds=sounds), letters=letters, strokes=strokes)
P["A"] = gr("Introduction to sounds", "Sounds, the sound wall and pre-writing strokes",
 [("/m/","mouse","lips together, voice on, continuous"),("/s/","sun","teeth together, quiet, continuous"),("/ă/","apple","mouth open wide, voice on, vowel"),("/p/","pig","lips together, quiet puff, stop sound")],
 ["Words are made of sounds. Today we will listen for the sounds in words and learn how our mouth makes them. Our sound wall shows a mouth picture and a key word for each sound.",
  "Some sounds can be stretched out (continuous sounds like /mmm/ and /sss/). Some sounds are quick (stop sounds like /p/). Some sounds turn the voice on (feel your throat hum for /m/); others are quiet (/s/, /p/).",
  "Introduce the routine hand gestures: stretch hands apart for a continuous sound, chop for a stop sound, touch the throat for a voiced sound."],
 [], ["Sky writing and tracing: big arm movements in the air, then trace shapes with a finger.","Circles: start at the top, go around to the left (anticlockwise) and back to the top.","Curves: half circle, smile and hump strokes - the building blocks of many letters (c, o, u, n, m)."],
 ["Getting Ready lessons introduce the 44 phonemes and letter formation. None of the content is expected to be mastered - the core lessons will review it."])
P["B"] = gr("Consonants: place of articulation", "Where in the mouth each consonant sound is made",
 [("/p/ /b/ /m/","pig, bee, mouse","lips together (bilabial)"),("/f/ /v/","fish, volcano","teeth on lip (labiodental)"),("/th/ /th/","thumb, this","tongue between teeth (interdental)"),("/t/ /d/ /n/ /s/ /z/","tiger, dog, nose, sun, zip","tongue behind top teeth (alveolar)"),("/sh/ /zh/ /ch/ /j/ /y/ /r/","sheep, treasure, chicken, jar, yellow, red","tongue lifted (palatal)"),("/k/ /g/ /ŋ/ /w/","kite, ghost, ring, watermelon","tongue pulled back (velar)"),("/h/","hat","back of throat (glottal)")],
 ["Consonant sounds are made by blocking or squeezing the air somewhere in the mouth. Today we will find out WHERE each sound is made. The sound wall groups consonants by the place in the mouth.",
  "Say each sound and feel it: /p/ /b/ /m/ use the lips together. /f/ /v/ put the teeth on the lip. /th/ puts the tongue between the teeth. /t/ /d/ /n/ /s/ /z/ put the tongue behind the top teeth. /sh/ /ch/ /j/ /y/ /r/ lift the tongue. /k/ /g/ /ŋ/ /w/ pull the tongue back. /h/ comes from the back of the throat."],
 [], ["Vertical lines: start at the top and pull straight down.","Horizontal lines: start on the left and go across to the right.","Slanted lines: down to the right (\\) and down to the left (/)."])
P["C"] = gr("Consonants: manner of articulation (stops and nasals)", "How the air is stopped or sent through the nose",
 [("/p/ /b/","pig, bee","stop sounds with the lips; /p/ quiet, /b/ voice on"),("/t/ /d/","tiger, dog","stop sounds with the tongue behind the teeth; /t/ quiet, /d/ voice on"),("/k/ /g/","kite, ghost","stop sounds with the tongue pulled back; /k/ quiet, /g/ voice on"),("/m/","mouse","nasal: lips together, air through the nose"),("/n/","nose","nasal: tongue behind top teeth, air through the nose"),("/ŋ/","ring","nasal: tongue pulled back, air through the nose")],
 ["Yesterday we learned WHERE sounds are made. Today we learn HOW the air moves. Stop sounds stop the air completely and then let it pop out: /p/ /b/ /t/ /d/ /k/ /g/. They are quick - do not add /uh/.",
  "Nasal sounds send the air out through the nose: /m/ /n/ /ŋ/. Hold your nose and try to say /mmm/ - you can't! Nasal sounds can be stretched out."],
 ["L","F","E"], ["Uppercase L: pull down, then across to the right.","Uppercase F: pull down, across at the top, across in the middle.","Uppercase E: pull down, across at the top, middle and bottom."])
P["D"] = gr("Consonants: fricatives and affricates", "Sounds made by squeezing the air",
 [("/f/ /v/","fish, volcano","fricative: teeth on lip; /f/ quiet, /v/ voice on"),("/th/ /th/","thumb, this","fricative: tongue between teeth; quiet / voice on"),("/s/ /z/","sun, zip","fricative: teeth together; /s/ quiet, /z/ voice on"),("/sh/ /zh/","sheep, treasure","fricative: lips round, tongue back; /sh/ quiet, /zh/ voice on"),("/h/","hat","fricative from the back of the throat, quiet"),("/ch/ /j/","chicken, jar","affricate: a stop then a squeeze; /ch/ quiet, /j/ voice on")],
 ["Fricative sounds squeeze the air through a small space so it makes friction - a hissing or buzzing: /f/ /v/ /th/ /s/ /z/ /sh/ /zh/ /h/. Rub your thumb and finger together for the friction gesture. These sounds can be stretched out.",
  "Affricate sounds start like a stop and end like a fricative: /ch/ and /j/. They are quick. Each pair has a quiet sound and a voiced sound - feel your throat."],
 ["H","T","I"], ["Uppercase H: two lines down, then across the middle.","Uppercase T: across the top, then down the middle.","Uppercase I: down, then a short line across the top and bottom."])
P["E"] = gr("Consonants: glides and liquids", "Sounds where the tongue moves smoothly",
 [("/y/","yellow","glide: tongue lifted, voice on"),("/w/","watermelon","glide: lips rounded, voice on"),("/l/","leaf","liquid: tongue behind top teeth, voice flows around the sides"),("/r/","red","liquid: tongue lifted and pulled back a little, voice on")],
 ["Glide and liquid sounds do not block the air much - the tongue comes close but the air flows freely. /y/ and /w/ are glides: the mouth glides into the next vowel. /l/ and /r/ are liquids. All four have the voice on.",
  "Practise saying /y/ and /w/ before vowels: /yă/, /wă/. Say /l/ and /r/ without adding /uh/: /lll/, /rrr/."],
 ["O","Q","C","G"], ["Uppercase O: start at the top and go around to the left.","Uppercase Q: like O, then add a short tail.","Uppercase C: start at the top, curve around to the left and stop.","Uppercase G: like C, then across and down."])
P["F"] = gr("Consonant review: place, manner and voice", "Reviewing all consonant sounds",
 [("Place","","lips together / teeth on lip / tongue between teeth / tongue behind teeth / tongue lifted / tongue pulled back / back of throat"),("Manner","","stops, nasals, fricatives, affricates, glides and liquids"),("Voiced","/b/ /d/ /g/ /m/ /n/ /ŋ/ /v/ /th/ /z/ /zh/ /j/ /y/ /w/ /l/ /r/","feel the throat hum"),("Unvoiced","/p/ /t/ /k/ /f/ /th/ /s/ /sh/ /h/ /ch/","quiet: no hum")],
 ["We review all the consonant sounds on the sound wall. For each sound: where is it made (place)? how does the air move (manner)? is the voice on or off? Use the hand gestures.",
  "Play 'find the sound': say a word, students find the sound wall card for the first sound."],
 ["U","J","S"], ["Uppercase U: down, curve, up.","Uppercase J: down, curve to the left.","Uppercase S: curve to the left, then to the right, like a snake."])
P["G"] = gr("Introduction to vowels", "Consonants block the air; vowels let it flow",
 [("/f/","fish","consonant: air squeezed"),("/ă/","apple","vowel: air flows freely, voice on"),("/p/","pig","consonant: air stopped"),("/n/","nose","consonant: air through the nose"),("/ō/","open","vowel: air flows, lips round"),("/ch/","chicken","consonant"),("/d/","dog","consonant"),("/k/","kite","consonant"),("/ĕ/","edge","vowel: air flows, mouth a little open")],
 ["There are two kinds of sounds. Consonant sounds block or squeeze the air somewhere in the mouth. Vowel sounds let the air flow out freely with the voice on - the mouth is open. Every word and every syllable has a vowel sound.",
  "Say each sound and decide: consonant or vowel? /fff/ - the air is squeezed: consonant. /ăăă/ - the air flows: vowel."],
 ["D","P","B","R"], ["Uppercase D: down, then a big curve from the top back to the bottom.","Uppercase P: down, then a small curve at the top.","Uppercase B: down, then two curves.","Uppercase R: down, a small curve at the top, then a slanted line down."])
P["H"] = gr("Vowels: the vowel valley", "Vowel sounds ordered by how open the mouth is",
 [("/ē/","eagle","smile, mouth almost closed"),("/ĭ/","itch","small smile"),("/ā/","acorn","mouth a little more open"),("/ĕ/","edge","more open"),("/ă/","apple","wide open"),("/ī/","ice cream","wide open then glide to a smile"),("/ŭ/","up","relaxed, open a little"),("/ŏ/","octopus","open and round"),("/ō/","open","round"),("/oo/","book","lips a little round, short"),("/yū/","unicorn","/y/ then round lips"),("/ū/","spoon","lips tightly round")],
 ["The vowel valley shows the vowel sounds in order. On the left side the mouth starts almost closed with a smile (/ē/) and opens wider and wider (/ĭ/, /ā/, /ĕ/, /ă/). At the bottom of the valley the mouth is wide open (/ī/, /ŭ/, /ŏ/). Going up the right side the lips get rounder and rounder (/ō/, /oo/, /yū/, /ū/).",
  "Say the vowels in order and feel your mouth open and then round: /ē/ /ĭ/ /ā/ /ĕ/ /ă/ /ī/ /ŭ/ /ŏ/ /ō/ /oo/ /yū/ /ū/."],
 ["K","M","N","A"], ["Uppercase K: down, then two slanted lines meeting in the middle.","Uppercase M: down, slant down, slant up, down.","Uppercase N: down, slant down, up.","Uppercase A: slant down to the left, slant down to the right, across the middle."])
P["I"] = gr("Vowels: schwa, diphthongs and r-controlled vowels", "The special vowel sounds",
 [("/ə/","above","schwa: quick, relaxed, unstressed"),("/oi/","oil","diphthong: /o/ glides to /i/"),("/ow/","owl","diphthong: /a/ glides to /oo/"),("/ar/","arm","r-controlled: open and relaxed"),("/er/","earth","r-controlled: mouth a little open, tongue pulled back"),("/or/","orange","r-controlled: lips round")],
 ["Some vowel sounds are special. The schwa /ə/ is the quick, relaxed vowel in unstressed syllables (the first sound in above). We do not stretch it.",
  "Diphthongs are two vowel sounds that glide together so fast we hear one sound: /oi/ (oil) and /ow/ (owl). Feel your mouth move.",
  "R-controlled vowels are vowel sounds changed by R: /ar/ (arm), /er/ (earth), /or/ (orange). In our accent we do not say the /r/ at the end."],
 ["V","W","X"], ["Uppercase V: slant down to the right, slant up to the right.","Uppercase W: down, up, down, up.","Uppercase X: slant down to the right, then slant down to the left."])
P["J"] = gr("Sound wall review: consonants and vowels", "Reviewing all 44 sounds",
 [("Consonants","","review by place, manner and voice"),("Vowels","","review the vowel valley, schwa, diphthongs and r-controlled vowels")],
 ["We review the whole sound wall. Say each sound with its key word and mouth picture. Sort sounds: consonant or vowel? voiced or unvoiced? stop or continuous?",
  "Play 'I spy a sound': give a sound; students find it on the wall and say a word that starts with it."],
 ["Y","Z"], ["Uppercase Y: two slanted lines meeting in the middle, then down.","Uppercase Z: across, slant down to the left, across."])
