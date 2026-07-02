<template>
  <g :transform="`translate(${x}, ${y}) scale(${scale})`">
    
    <!-- ============================================ -->
    <!--     BASIC BUBBLES (BURBUJAS SIMPLES)        -->
    <!-- ============================================ -->

    <!-- SINGLE RECEIVED -->
    <g v-if="type === 'chat-single-received'">
      <path d="M20,10 L250,10 Q260,10 260,20 L260,50 Q260,60 250,60 L35,60 L20,75 L20,60 L20,20 Q20,10 30,10 Z" 
            fill="#e5e5ea" stroke="none"/>
      <text x="35" y="40" font-family="SF Pro, Arial, sans-serif" font-size="14" fill="#000">
        Are you coming to the party tonight?
      </text>
    </g>

    <!-- SINGLE SENT -->
    <g v-if="type === 'chat-single-sent'">
      <path d="M40,10 L270,10 Q280,10 280,20 L280,60 L280,75 L265,60 L50,60 Q40,60 40,50 L40,20 Q40,10 50,10 Z" 
            fill="#007aff" stroke="none"/>
      <text x="55" y="40" font-family="SF Pro, Arial, sans-serif" font-size="14" fill="#ffffff">
        Yes! I'll be there at 8pm
      </text>
    </g>

    <!-- CONVERSATION SIMPLE -->
    <g v-if="type === 'chat-conversation-simple'">
      <!-- Received -->
      <path d="M15,15 L220,15 Q230,15 230,25 L230,55 Q230,65 220,65 L30,65 L15,80 L15,65 L15,25 Q15,15 25,15 Z" 
            fill="#e5e5ea" stroke="none"/>
      <text x="30" y="45" font-family="SF Pro, Arial, sans-serif" font-size="13" fill="#000">
        Hey! What time is the meeting?
      </text>
      <!-- Sent -->
      <path d="M90,90 L295,90 Q305,90 305,100 L305,140 L305,155 L290,140 L100,140 Q90,140 90,130 L90,100 Q90,90 100,90 Z" 
            fill="#007aff" stroke="none"/>
      <text x="105" y="120" font-family="SF Pro, Arial, sans-serif" font-size="13" fill="#ffffff">
        It's at 3pm in Room 204
      </text>
    </g>

    <!-- ============================================ -->
    <!--     PLATFORM STYLES (ESTILOS APPS)          -->
    <!-- ============================================ -->

    <!-- WHATSAPP STYLE -->
    <g v-if="type === 'whatsapp-chat'">
      <rect x="0" y="0" width="320" height="280" fill="#ece5dd"/>
      <!-- Pattern placeholder (dots) -->
      <g opacity="0.1">
         <circle cx="20" cy="20" r="2" fill="#000" />
         <circle cx="300" cy="20" r="2" fill="#000" />
         <circle cx="20" cy="260" r="2" fill="#000" />
         <circle cx="300" cy="260" r="2" fill="#000" />
         <circle cx="160" cy="140" r="2" fill="#000" />
      </g>
      <!-- Header -->
      <rect x="0" y="0" width="320" height="50" fill="#075e54"/>
      <circle cx="35" cy="25" r="18" fill="#128c7e"/>
      <text x="35" y="30" text-anchor="middle" font-family="Arial" font-size="14" fill="#fff">M</text>
      <text x="65" y="22" font-family="Arial" font-size="14" font-weight="bold" fill="#fff">Mom</text>
      <text x="65" y="38" font-family="Arial" font-size="11" fill="#a8d4cf">online</text>
      <!-- Msg Received -->
      <g transform="translate(10, 60)">
        <path d="M8,0 L200,0 Q210,0 210,10 L210,45 Q210,55 200,55 L15,55 L0,65 L5,55 Q8,55 8,45 Z" 
              fill="#ffffff" stroke="none"/>
        <text x="18" y="22" font-family="Arial" font-size="13" fill="#303030">Don't forget to buy milk</text>
        <text x="18" y="40" font-family="Arial" font-size="13" fill="#303030">on your way home</text>
        <text x="185" y="50" font-family="Arial" font-size="9" fill="#999">10:30</text>
      </g>
      <!-- Msg Sent -->
      <g transform="translate(100, 140)">
        <path d="M0,0 L195,0 Q205,0 205,10 L205,35 Q205,45 195,45 L15,45 L10,55 L10,45 Q0,45 0,35 Z" 
              fill="#dcf8c6" stroke="none"/>
        <text x="15" y="28" font-family="Arial" font-size="13" fill="#303030">Ok! Anything else?</text>
        <text x="165" y="40" font-family="Arial" font-size="9" fill="#999">10:32</text>
        <g transform="translate(185, 36)">
          <path d="M0,0 L3,3 L8,-3" fill="none" stroke="#53bdeb" stroke-width="1.5"/>
          <path d="M4,0 L7,3 L12,-3" fill="none" stroke="#53bdeb" stroke-width="1.5"/>
        </g>
      </g>
      <!-- Msg Received 2 -->
      <g transform="translate(10, 200)">
        <path d="M8,0 L180,0 Q190,0 190,10 L190,35 Q190,45 180,45 L15,45 L0,55 L5,45 Q8,45 8,35 Z" 
              fill="#ffffff" stroke="none"/>
        <text x="18" y="28" font-family="Arial" font-size="13" fill="#303030">Some bread please 🍞</text>
        <text x="160" y="40" font-family="Arial" font-size="9" fill="#999">10:33</text>
      </g>
    </g>

    <!-- IMESSAGE STYLE -->
    <g v-if="type === 'imessage-chat'">
      <rect x="0" y="0" width="320" height="260" fill="#ffffff"/>
      <rect x="0" y="0" width="320" height="55" fill="#f6f6f6"/>
      <line x1="0" y1="55" x2="320" y2="55" stroke="#e0e0e0" stroke-width="1"/>
      <circle cx="160" cy="22" r="16" fill="#007aff"/>
      <text x="160" y="27" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">J</text>
      <text x="160" y="48" text-anchor="middle" font-family="SF Pro, Arial" font-size="13" font-weight="bold" fill="#000">John</text>
      <text x="160" y="80" text-anchor="middle" font-family="Arial" font-size="11" fill="#8e8e93">Today 2:45 PM</text>
      <!-- Msg 1 -->
      <g transform="translate(10, 95)">
        <rect x="0" y="0" width="200" height="40" rx="18" fill="#e5e5ea"/>
        <text x="18" y="26" font-family="SF Pro, Arial" font-size="14" fill="#000">Want to grab lunch?</text>
      </g>
      <!-- Msg 2 -->
      <g transform="translate(110, 145)">
        <rect x="0" y="0" width="195" height="40" rx="18" fill="#007aff"/>
        <text x="18" y="26" font-family="SF Pro, Arial" font-size="14" fill="#fff">Sure! Where do you want to go?</text>
      </g>
      <!-- Msg 3 -->
      <g transform="translate(10, 195)">
        <rect x="0" y="0" width="220" height="40" rx="18" fill="#e5e5ea"/>
        <text x="18" y="26" font-family="SF Pro, Arial" font-size="14" fill="#000">How about the new Italian place?</text>
      </g>
    </g>

    <!-- MESSENGER STYLE -->
    <g v-if="type === 'messenger-chat'">
      <rect x="0" y="0" width="320" height="280" fill="#ffffff"/>
      <rect x="0" y="0" width="320" height="60" fill="#ffffff"/>
      <line x1="0" y1="60" x2="320" y2="60" stroke="#e4e6eb" stroke-width="1"/>
      <circle cx="40" cy="30" r="20" fill="#1877f2"/>
      <text x="40" y="35" text-anchor="middle" font-family="Arial" font-size="14" fill="#fff">S</text>
      <circle cx="52" cy="42" r="6" fill="#31a24c" stroke="#fff" stroke-width="2"/>
      <text x="75" y="27" font-family="Arial" font-size="15" font-weight="bold" fill="#050505">Sarah</text>
      <text x="75" y="43" font-family="Arial" font-size="12" fill="#65676b">Active now</text>
      <!-- Msg 1 -->
      <g transform="translate(10, 75)">
        <circle cx="15" cy="35" r="14" fill="#1877f2"/>
        <text x="15" y="40" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">S</text>
        <rect x="35" y="0" width="180" height="50" rx="18" fill="#e4e6eb"/>
        <text x="52" y="22" font-family="Arial" font-size="13" fill="#050505">Did you finish the</text>
        <text x="52" y="40" font-family="Arial" font-size="13" fill="#050505">homework yet?</text>
      </g>
      <!-- Msg 2 -->
      <g transform="translate(100, 140)">
        <rect x="0" y="0" width="205" height="35" rx="18" fill="#0084ff"/>
        <text x="18" y="24" font-family="Arial" font-size="13" fill="#fff">Almost done! Just one more question</text>
      </g>
      <!-- Msg 3 -->
      <g transform="translate(10, 190)">
        <circle cx="15" cy="20" r="14" fill="#1877f2"/>
        <text x="15" y="25" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">S</text>
        <rect x="35" y="0" width="140" height="35" rx="18" fill="#e4e6eb"/>
        <text x="52" y="24" font-family="Arial" font-size="13" fill="#050505">Can I see it? 📚</text>
      </g>
      <!-- Typing -->
      <g transform="translate(10, 240)">
        <circle cx="15" cy="15" r="14" fill="#1877f2"/>
        <text x="15" y="20" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">S</text>
        <rect x="35" y="0" width="60" height="30" rx="15" fill="#e4e6eb"/>
        <circle cx="52" cy="15" r="4" fill="#65676b">
          <animate attributeName="opacity" values="0.3;1;0.3" dur="1s" repeatCount="indefinite"/>
        </circle>
        <circle cx="65" cy="15" r="4" fill="#65676b">
          <animate attributeName="opacity" values="0.3;1;0.3" dur="1s" repeatCount="indefinite" begin="0.2s"/>
        </circle>
        <circle cx="78" cy="15" r="4" fill="#65676b">
          <animate attributeName="opacity" values="0.3;1;0.3" dur="1s" repeatCount="indefinite" begin="0.4s"/>
        </circle>
      </g>
    </g>

    <!-- SMS STYLE -->
    <g v-if="type === 'sms-conversation'">
      <rect x="0" y="0" width="300" height="220" fill="#f5f5f5"/>
      <rect x="0" y="0" width="300" height="45" fill="#4a4a4a"/>
      <text x="150" y="28" text-anchor="middle" font-family="Arial" font-size="14" fill="#fff">+1 (555) 123-4567</text>
      <!-- Msg 1 -->
      <g transform="translate(15, 60)">
        <rect x="0" y="0" width="180" height="45" rx="8" fill="#ffffff" stroke="#ddd" stroke-width="1"/>
        <text x="12" y="20" font-family="Arial" font-size="12" fill="#333">Running late. Traffic is bad.</text>
        <text x="12" y="38" font-family="Arial" font-size="10" fill="#999">3:45 PM</text>
      </g>
      <!-- Msg 2 -->
      <g transform="translate(95, 120)">
        <rect x="0" y="0" width="190" height="45" rx="8" fill="#34b7f1" stroke="none"/>
        <text x="12" y="20" font-family="Arial" font-size="12" fill="#fff">No problem. Take your time!</text>
        <text x="155" y="38" font-family="Arial" font-size="10" fill="#c5e8f7">3:47 PM</text>
      </g>
      <!-- Msg 3 -->
      <g transform="translate(15, 180)">
        <rect x="0" y="0" width="120" height="30" rx="8" fill="#ffffff" stroke="#ddd" stroke-width="1"/>
        <text x="12" y="20" font-family="Arial" font-size="12" fill="#333">Thanks! 🙏</text>
      </g>
    </g>

    <!-- ============================================ -->
    <!--     RICH MEDIA CHATS (MULTIMEDIA)           -->
    <!-- ============================================ -->

    <!-- CHAT WITH IMAGE -->
    <g v-if="type === 'chat-with-image'">
      <rect x="0" y="0" width="320" height="250" fill="#ece5dd"/>
      <!-- Msg Received -->
      <g transform="translate(10, 15)">
        <rect x="0" y="0" width="200" height="160" rx="10" fill="#ffffff"/>
        <!-- Placeholder img -->
        <rect x="8" y="8" width="184" height="110" rx="6" fill="#e0e0e0"/>
        <g transform="translate(100, 63)">
          <rect x="-30" y="-20" width="60" height="40" rx="4" fill="#bdbdbd"/>
          <circle cx="-15" cy="-8" r="6" fill="#9e9e9e"/>
          <polygon points="-25,15 -5,-5 10,10 25,-2 25,15" fill="#9e9e9e"/>
        </g>
        <text x="15" y="138" font-family="Arial" font-size="12" fill="#303030">Look what I found! 😍</text>
        <text x="170" y="152" font-family="Arial" font-size="9" fill="#999">2:30 PM</text>
      </g>
      <!-- Msg Sent -->
      <g transform="translate(120, 190)">
        <rect x="0" y="0" width="185" height="40" rx="18" fill="#dcf8c6"/>
        <text x="15" y="26" font-family="Arial" font-size="13" fill="#303030">Wow! Where is that?</text>
        <text x="145" y="35" font-family="Arial" font-size="9" fill="#999">2:31 PM</text>
      </g>
    </g>

    <!-- CHAT VOICE MESSAGE -->
    <g v-if="type === 'chat-voice-message'">
      <rect x="0" y="0" width="320" height="120" fill="#ece5dd"/>
      <g transform="translate(10, 20)">
        <rect x="0" y="0" width="240" height="55" rx="25" fill="#ffffff"/>
        <circle cx="30" cy="27" r="18" fill="#128c7e"/>
        <text x="30" y="32" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff">A</text>
        <circle cx="70" cy="27" r="14" fill="#128c7e"/>
        <polygon points="67,20 67,34 80,27" fill="#fff"/>
        <g transform="translate(95, 27)">
          <rect x="0" y="-8" width="3" height="16" rx="1" fill="#128c7e"/>
          <rect x="6" y="-12" width="3" height="24" rx="1" fill="#128c7e"/>
          <rect x="12" y="-6" width="3" height="12" rx="1" fill="#128c7e"/>
          <rect x="18" y="-15" width="3" height="30" rx="1" fill="#128c7e"/>
          <rect x="24" y="-8" width="3" height="16" rx="1" fill="#128c7e"/>
          <rect x="30" y="-12" width="3" height="24" rx="1" fill="#128c7e"/>
          <rect x="36" y="-5" width="3" height="10" rx="1" fill="#128c7e"/>
          <rect x="42" y="-10" width="3" height="20" rx="1" fill="#128c7e"/>
          <rect x="48" y="-7" width="3" height="14" rx="1" fill="#128c7e"/>
          <rect x="54" y="-12" width="3" height="24" rx="1" fill="#128c7e"/>
          <rect x="60" y="-6" width="3" height="12" rx="1" fill="#128c7e"/>
          <rect x="66" y="-10" width="3" height="20" rx="1" fill="#128c7e"/>
          <rect x="72" y="-4" width="3" height="8" rx="1" fill="#128c7e"/>
        </g>
        <text x="200" y="32" font-family="Arial" font-size="11" fill="#999">0:42</text>
        <text x="215" y="48" font-family="Arial" font-size="9" fill="#999">11:20</text>
      </g>
    </g>

    <!-- CHAT GROUP -->
    <g v-if="type === 'chat-group'">
      <rect x="0" y="0" width="320" height="300" fill="#ece5dd"/>
      <rect x="0" y="0" width="320" height="55" fill="#075e54"/>
      <g transform="translate(35, 27)">
        <circle cx="0" cy="0" r="16" fill="#25d366"/>
        <circle cx="12" cy="0" r="16" fill="#128c7e" stroke="#075e54" stroke-width="2"/>
        <circle cx="24" cy="0" r="16" fill="#34b7f1" stroke="#075e54" stroke-width="2"/>
      </g>
      <text x="75" y="22" font-family="Arial" font-size="14" font-weight="bold" fill="#fff">Study Group 📚</text>
      <text x="75" y="40" font-family="Arial" font-size="11" fill="#a8d4cf">Anna, Mike, Sarah</text>
      <!-- Msg Anna -->
      <g transform="translate(10, 65)">
        <text x="10" y="12" font-family="Arial" font-size="11" font-weight="bold" fill="#25d366">Anna</text>
        <rect x="0" y="18" width="200" height="40" rx="8" fill="#ffffff"/>
        <text x="12" y="42" font-family="Arial" font-size="12" fill="#303030">When is the exam?</text>
        <text x="170" y="52" font-family="Arial" font-size="9" fill="#999">9:15</text>
      </g>
      <!-- Msg Mike -->
      <g transform="translate(10, 130)">
        <text x="10" y="12" font-family="Arial" font-size="11" font-weight="bold" fill="#128c7e">Mike</text>
        <rect x="0" y="18" width="160" height="40" rx="8" fill="#ffffff"/>
        <text x="12" y="42" font-family="Arial" font-size="12" fill="#303030">Next Monday at 9am</text>
        <text x="125" y="52" font-family="Arial" font-size="9" fill="#999">9:16</text>
      </g>
      <!-- My Msg -->
      <g transform="translate(100, 195)">
        <rect x="0" y="0" width="205" height="40" rx="8" fill="#dcf8c6"/>
        <text x="12" y="26" font-family="Arial" font-size="12" fill="#303030">Thanks! Should we study together?</text>
        <text x="165" y="35" font-family="Arial" font-size="9" fill="#999">9:17</text>
      </g>
      <!-- Msg Sarah -->
      <g transform="translate(10, 250)">
        <text x="10" y="12" font-family="Arial" font-size="11" font-weight="bold" fill="#34b7f1">Sarah</text>
        <rect x="0" y="18" width="130" height="30" rx="8" fill="#ffffff"/>
        <text x="12" y="38" font-family="Arial" font-size="12" fill="#303030">Great idea! 👍</text>
      </g>
    </g>

    <!-- CHAT INVITATION -->
    <g v-if="type === 'chat-invitation'">
      <rect x="0" y="0" width="320" height="200" fill="#ffffff"/>
      <g transform="translate(15, 20)">
        <rect x="0" y="0" width="250" height="150" rx="12" fill="#e5e5ea"/>
        <rect x="10" y="10" width="230" height="100" rx="8" fill="#ffffff" stroke="#e0e0e0" stroke-width="1"/>
        <rect x="25" y="25" width="40" height="40" rx="6" fill="#007aff"/>
        <text x="45" y="42" text-anchor="middle" font-family="Arial" font-size="10" fill="#fff">SAT</text>
        <text x="45" y="58" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="#fff">15</text>
        <text x="80" y="38" font-family="Arial" font-size="13" font-weight="bold" fill="#000">Birthday Party 🎉</text>
        <text x="80" y="55" font-family="Arial" font-size="11" fill="#666">Saturday, March 15</text>
        <text x="80" y="72" font-family="Arial" font-size="11" fill="#666">7:00 PM - 11:00 PM</text>
        <text x="80" y="95" font-family="Arial" font-size="11" fill="#007aff">📍 123 Main Street</text>
        <text x="15" y="130" font-family="Arial" font-size="13" fill="#000">Can you come?</text>
        <text x="210" y="142" font-family="Arial" font-size="10" fill="#999">10:30 AM</text>
      </g>
    </g>

    <!-- CHAT LOCATION -->
    <g v-if="type === 'chat-location'">
      <rect x="0" y="0" width="320" height="180" fill="#ece5dd"/>
      <g transform="translate(10, 15)">
        <rect x="0" y="0" width="220" height="140" rx="10" fill="#ffffff"/>
        <rect x="8" y="8" width="204" height="90" rx="6" fill="#e8f4e8"/>
        <line x1="8" y1="50" x2="212" y2="50" stroke="#fff" stroke-width="3"/>
        <line x1="60" y1="8" x2="60" y2="98" stroke="#fff" stroke-width="3"/>
        <line x1="150" y1="8" x2="150" y2="98" stroke="#fff" stroke-width="3"/>
        <g transform="translate(110, 50)">
          <ellipse cx="0" cy="12" rx="8" ry="4" fill="rgba(0,0,0,0.2)"/>
          <path d="M0,-20 C-12,-20 -12,0 0,15 C12,0 12,-20 0,-20" fill="#e74c3c"/>
          <circle cx="0" cy="-12" r="5" fill="#fff"/>
        </g>
        <text x="15" y="115" font-family="Arial" font-size="11" font-weight="bold" fill="#303030">Central Park</text>
        <text x="15" y="130" font-family="Arial" font-size="10" fill="#666">Meeting point 📍</text>
        <text x="185" y="132" font-family="Arial" font-size="9" fill="#999">3:45</text>
      </g>
    </g>

    <!-- CHAT QUESTION RESPONSE (ICFES STYLE) -->
    <g v-if="type === 'chat-question-response'">
      <rect x="0" y="0" width="320" height="180" fill="#f0f0f0"/>
      <rect x="100" y="10" width="120" height="20" rx="10" fill="#e0e0e0"/>
      <text x="160" y="24" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">Text message</text>
      <!-- Msg 1 -->
      <g transform="translate(15, 45)">
        <rect x="0" y="0" width="200" height="45" rx="18" fill="#e5e5ea"/>
        <text x="18" y="20" font-family="Arial" font-size="13" fill="#000">Do you want to go to the</text>
        <text x="18" y="38" font-family="Arial" font-size="13" fill="#000">cinema tomorrow?</text>
      </g>
      <!-- Msg 2 incomplete -->
      <g transform="translate(105, 105)">
        <rect x="0" y="0" width="200" height="45" rx="18" fill="#007aff"/>
        <text x="18" y="30" font-family="Arial" font-size="13" fill="#ffffff">_________________</text>
      </g>
      <text x="160" y="170" text-anchor="middle" font-family="Arial" font-size="10" fill="#999">What would be the best response?</text>
    </g>

    <!-- CHAT EMOJI REACTION -->
    <g v-if="type === 'chat-emoji-reaction'">
      <rect x="0" y="0" width="320" height="150" fill="#ece5dd"/>
      <g transform="translate(10, 25)">
        <rect x="0" y="0" width="220" height="50" rx="10" fill="#ffffff"/>
        <text x="15" y="22" font-family="Arial" font-size="13" fill="#303030">I got the job! 🎉</text>
        <text x="15" y="42" font-family="Arial" font-size="13" fill="#303030">Starting next month!</text>
        <text x="190" y="45" font-family="Arial" font-size="9" fill="#999">4:20</text>
        <!-- Reactions -->
        <g transform="translate(180, 45)">
          <rect x="0" y="0" width="50" height="24" rx="12" fill="#ffffff" stroke="#e0e0e0" stroke-width="1"/>
          <text x="12" y="17" font-family="Arial" font-size="14">🎉</text>
          <text x="32" y="17" font-family="Arial" font-size="11" fill="#666">3</text>
        </g>
      </g>
      <g transform="translate(90, 95)">
        <rect x="0" y="0" width="215" height="35" rx="18" fill="#dcf8c6"/>
        <text x="15" y="24" font-family="Arial" font-size="13" fill="#303030">Congratulations!! So happy for you!</text>
      </g>
    </g>

    <!-- CHAT READ RECEIPTS -->
    <g v-if="type === 'chat-read-receipts'">
      <rect x="0" y="0" width="320" height="200" fill="#ece5dd"/>
      <!-- Read -->
      <g transform="translate(100, 20)">
        <rect x="0" y="0" width="205" height="40" rx="8" fill="#dcf8c6"/>
        <text x="15" y="26" font-family="Arial" font-size="13" fill="#303030">Are you free this weekend?</text>
        <text x="155" y="35" font-family="Arial" font-size="9" fill="#999">10:30</text>
        <g transform="translate(185, 30)">
          <path d="M0,0 L3,3 L8,-3" fill="none" stroke="#53bdeb" stroke-width="1.5"/>
          <path d="M4,0 L7,3 L12,-3" fill="none" stroke="#53bdeb" stroke-width="1.5"/>
        </g>
      </g>
      <!-- Delivered -->
      <g transform="translate(120, 75)">
        <rect x="0" y="0" width="185" height="40" rx="8" fill="#dcf8c6"/>
        <text x="15" y="26" font-family="Arial" font-size="13" fill="#303030">Let me know! 😊</text>
        <text x="130" y="35" font-family="Arial" font-size="9" fill="#999">10:31</text>
        <g transform="translate(160, 30)">
          <path d="M0,0 L3,3 L8,-3" fill="none" stroke="#999" stroke-width="1.5"/>
          <path d="M4,0 L7,3 L12,-3" fill="none" stroke="#999" stroke-width="1.5"/>
        </g>
      </g>
      <!-- Sent -->
      <g transform="translate(140, 130)">
        <rect x="0" y="0" width="165" height="40" rx="8" fill="#dcf8c6"/>
        <text x="15" y="26" font-family="Arial" font-size="13" fill="#303030">Hello? 👋</text>
        <text x="105" y="35" font-family="Arial" font-size="9" fill="#999">10:45</text>
        <g transform="translate(135, 30)">
          <path d="M0,0 L4,4 L12,-6" fill="none" stroke="#999" stroke-width="1.5"/>
        </g>
      </g>
      <g transform="translate(20, 185)">
        <text x="0" y="0" font-family="Arial" font-size="9" fill="#666">✓ Sent  ✓✓ Delivered  </text>
        <text x="115" y="0" font-family="Arial" font-size="9" fill="#53bdeb">✓✓ Read</text>
      </g>
    </g>

    <!-- Label opcional -->
    <text
      v-if="label"
      x="160"
      y="240"
      font-family="sans-serif"
      font-size="14"
      font-weight="bold"
      fill="#374151"
      text-anchor="middle"
    >
      {{ label }}
    </text>

  </g>
</template>

<script setup>
import { computed } from 'vue';

const props = defineProps({
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  width: { type: Number, default: 320 }, // Ancho base estándar para chats
  type: { type: String, default: 'chat-single-received' },
  label: { type: String, default: '' }
});

// Calculamos escala basada en el ancho deseado
const scale = computed(() => {
  return props.width / 320;
});
</script>
