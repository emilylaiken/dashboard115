// Google Map
var map;

// Hold marker and path objects
var james_marks = [];
var james_paths = [];
var james_infos = [];
var hemingway_marks = [];
var hemingway_paths = [];
var hemingway_infos = [];
var cather_marks = [];
var cather_paths = [];
var cather_infos = [];



//Places
var albany = {lat: 42.6526, lng: -73.7562};
var florence = {lat: 43.7696, lng: 11.2558};
var rome = {lat: 41.9028, lng: 12.4964};
var gardencourt = {lat: 52.7907, lng: -2.8563};
var paris = {lat: 48.8566, lng: 2.3522};
var pamplona = {lat: 42.8125, lng: -1.6458};
var burguete = {lat: 42.9905, lng: -1.3355};
var madrid = {lat: 40.4168, lng: -3.7038};
var princeton = {lat: 40.3573, lng: -74.6672};
var new_york = {lat: 40.7128, lng: -74.0059};
var black_hawk = {lat: 40.0890, lng: -98.5196};
var bohemia = {lat: 50.0755, lng: 14.4378};
var virginia = {lat: 37.5407, lng: -77.4360};
var lincoln = {lat: 40.8258, lng: -96.6852};

var albany_quotes = 
[
    "\"American girls were used to a great deal of deference, and it had been intimated that this one had a high spirit. (16)\" ",
    "\"You can't stay alone with the gentleman. You are not--you are not at Albany, my dear.\" (69)"
]

var albany_images = 
[
    '<img src="http://williamgmuller.com/images/prints/albany.jpg" height=200 width=340 align=left>',
    '<img src="http://4.bp.blogspot.com/-kkWJOkdEHGk/VhcjPfWvhlI/AAAAAAAAD_Y/p5_B79HhQzU/s1600/79.%2BNew%2BYork%2B1900.jpg" height=200 width=290 align=right>',
]

var gardencourt_quotes = 
[
    "\"Oh, I hoped there would be a lord; it's just like a novel!\" (16)",
    "\'I was glad to think of him between those thick walls at Gardencourt' [said Isabel]. 'He was completely alone there; the thick walls were his only company' [said Lord Warburton].\" (404)"
]

var gardencourt_images = 
[
    '<img src="http://chestofbooks.com/gardening-horticulture/Design-Landscape-Gardening/images/Figure-49-MONTACUTE-HOUSE-A-typical-English-country-estate.jpg" height=210 width=320 aligh=left>',
    '<img src="http://www.cummermuseum.org/sites/default/files/images/cma_visit_gardens_nina_cummer.jpg" height=210 width=270 align=right>',
]

var rome_quotes =
[
    "\"On such occasions she had several resorts; the most accessable of which perhaps was a seat on the low parapet which edges the grassy space lying before the high, cold front of St. John Lateran; where you look across the Campagna at the far-trailing outline of the Alban Mount, and at that mighty plain between, which is still so full of all that has vanished from it.\" (546)",
    "\"The carriage, passing out of the walls of Rome, rolled through narrow lanes...she strolled further and further over the flower-freckled turf, or sat on a stone that had once had a use, and gazed through the veil of her personal sadness at the splendid sadness of the scene.\" (546)"
]

var rome_images = 
[
    '<img src="https://wallpaperscraft.com/image/italy_rome_ruins_colosseum_ancient_black_white_10828_3840x2400.jpg" height=200 width=300 align=left>',
     '<img src="http://www.danheller.com/images/Europe/Turkey/Phaselis/roman-ruins-4.jpg" height=200 width=350 align=right>',
]

var florence_quotes =
[
    "\"My dear girl, I can't tell you how life seems to stretch there before us--what a long summer afternoon awaits us. It's the latter half of an Italian day--a golden haze, and the shadows just lengthening, and that divine delicacy in the light, the air, the landscape...\" (371)."
]

var florence_images = 
[
    '<img src="http://www.bretculp.com/gallery/ME/content/images/large/Bret-Culp_Italian-Villa-Morning-Fog-Tuscany-Italy.jpg" height=180 width=360 align=left>',
    '<img src="https://66.media.tumblr.com/4e3ea1826db2220dbfbb85fad7e6478a/tumblr_nt8ejpWr251tphleno1_500.jpg" height=180 width=250 hspace=20>',
]

var paris_quotes =
[
    "\"\'No, I don’t like Paris. It’s expensive and dirty.\' \'Really? I find it so extraordinarily clean. One of the cleanest cities in all Europe.\' \'I find it dirty.\' \'How strange! But perhaps you have not been here very long.\' \'I’ve been here long enough.\'\" (26)",
    "\"You're an expatriate. You've lost touch with the soil. You get precious. Fake European standards have ruined you. You drink yourself to death. You become obsessed with sex. You spend all your time talking, not working. You are an expatriate, see? You hang around cafes.\" (120)"
]


var paris_images = 
[
    '<img src="http://beta.costtodrive.com/wp-content/uploads/2013/07/Paris.jpg" height=170 width=200 aligh=left>',
    '<img src="http://blog.ebyline.com/wp-content/uploads/2013/09/paris-cafe2.jpg", height=170 width=430 align=right>'
]

var burguete_quotes =
[
    "\"In the Basque country the land all looks very rich and green and the houses and villages look well-off and clean… the houses in the villages had red tiled roofs, and then the road turned off and commenced to climb and we were going way up close along a hillside, with a valley below and hills stretched off back toward the sea.\" (99)",
    "\"We stayed five days at Burguete and had good fishing.\" (129)"
]

var burguete_images = 
[
    '<img src="http://media.gettyimages.com/photos/aerial-view-of-towns-of-les-escalades-and-andorra-nestling-in-valley-picture-id50510774" height=120 width=200>',
     '<img src="http://theplanetd.com/images/In-Pyrenees-10.jpg" height=120 width=180 hspace=25>',
     '<img src="http://greenweddingshoes.com/wp-content/uploads/2015/11/frenchpyrenees-wedding-28.jpg" height=120 width=220>'
]

var pamplona_quotes =
[
    "\"'You hear? Muerto. Dead. He's dead. With a horn through him. All for morning fun. Es muy flamenco.' 'It's bad.' 'Not for me,' the waiter said. 'No fun in that for me.'\" (202)"
]

var pamplona_images = 
[
   '<img src="https://s-media-cache-ak0.pinimg.com/236x/ea/5b/dd/ea5bdddfdf386632afeccf593070b778.jpg" height=200 width=150>',
   '<img src="https://timedotcom.files.wordpress.com/2016/07/pamplona.jpeg?quality=85&w=1100" height=200 width=250 hspace=35>',
   '<img src="http://sanfermin.pamplona.es/img/encierro_1932_ruperez_g.jpg" height=200 width=170>'
]

var madrid_quotes = 
[
    "\"'Don't get drunk, Jake' she said. 'You don't have to.' 'How do you know?' 'Don't,' she said. 'You'll be all right.' 'I'm not getting drunk,' I said. 'I'm just drinking a little wine. I like to drink wine.' 'Don't get drunk,' she said. 'Jake, don't get drunk.' 'Want to go for a ride?' I said. 'Want to ride through the town?' 'Right,' Brett said. 'I haven't seen Madrid. I should see Madrid.'\" (250)"
]

var madrid_images = 
[
    '<img src="https://c1.staticflickr.com/5/4014/4583338072_91ac836409_z.jpg" height=200 width=290>',
    '<img src="https://upload.wikimedia.org/wikipedia/commons/d/d6/Hotel-florida_1920.jpg" height=200 width=350 align=right>'
]

var princeton_quotes =
[
    "\"The letters were from the States. One was a bank statement....the other letter was a wedding announcement. Mr. and Mrs. Aloysius Kirby announce the marriage of their daughter Katherine--I knew neither the girl nor the man she was marrying. They must be circularizing the town.\" (37-38)"
]

var princeton_images = 
[
     '<img src="https://etcweb.princeton.edu/campusimages/34-10.jpeg" height=160 width=320 hspace=10>',
     '<img src="http://www.rantpolitical.com/wp-content/uploads/2014/10/Americans-in-WWI1.png" height=160 width=240 hspace=10>'
]

var bohemia_quotes =
[
    "It makes me homesick, Jimmy, this flower, this smell...we have this flower very much at home, in the old country. It always grew in our yard and my papa had a green bench and a table under the bushes. In summer, when they were in bloom, he used to sit there with his friend that played the trombone. When I was little I used to go down there to hear them talk--beautiful talk, like what I never hear in this country.\" (180)"
]

var bohemia_images = 
[
    '<img src="http://www.judnick.com/images/Bohemia200img178_small.jpg" height=130 width=200>',
    '<img src="http://www.shevchukart.com/img/gallery/1336.jpeg" height=130 width=440 align=right>',
    
]

var blackhawk_quotes =
[
    "\"There was nothing but land: not a country at all, but the material out of which countries are made...I had the feeling that the world was left behind, that we had got over the edge of it, and were outside man's jurisdiction.\" (12)",
    "\"Between that earth and that sky I felt erased, blotted out. I did not say my prayers that night: here, I felt, what would be, would be.\" (13)"
]

var blackhawk_images = 
[
    '<img src="http://2.bp.blogspot.com/_v0xZjSOH67Y/TMZYIjIpdTI/AAAAAAAAAPI/JcfH21KAU5M/s1600/Nebraska+Prairie.jpg" height=140 width=240>',
    '<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Homesteader_NE_1866.png/315px-Homesteader_NE_1866.png" height=140 width=190 hspace=15>',
    '<img src="http://www.composingkate.com/wp-content/uploads/2012/10/Nebraska-Sunrise-by-Shannon-Patrick.jpg" height=140 width=190>',
]

var lincoln_quotes =
[
    "\"I shall always look back on that time of mental awakening as one of the happiest in my life. Gaston Cleric introduced me to the world of ideas; when one first eneters that world everything else fades for a time, and all that went before is as if it had not been.\" (195)",
    "\"I worked at a commodious green-topped table placed directly in front of the west window whcih looked out over the prairie. In the corner at my right were all my books, in shelves I had made and painted myself.\" (196)"
]

var lincoln_images = 
[
    '<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Omaha_Nebraska_c1914_LOC_6a13849u.jpg/800px-Omaha_Nebraska_c1914_LOC_6a13849u.jpg" height=120 width=650>',
]

var virginia_quotes =
[
    "\"I did not believe that my dead father and mother were watching me from up there; they would still be looking for me at the sheep-fold down by the creek, or along the white road that led to the mountains pastures. I had left even their spirits behind me.\" (13)" 
]

var virginia_images = 
[
    '<img src="http://www.leesburgva.gov/Home/ShowImage?id=1030&t=635477178326200000" height=200 width=210>',
    '<img src="http://www.asuddenlight.com/wp-content/uploads/2014/09/Seattle_-_Railroad_Avenue_-_1900.jpg" height=200 width=430 align=right>',
]

var newyork_quotes = []

var newyork_images = 
[
    '<img src="https://www.favrify.com/wp-content/uploads/2015/01/235.jpg" height=180 width=650>'
]

var albany_self = 'Isabel associates Albany with her “happiest memor[ies]” of her Grandmother’s “large hospitality” (23) in the days of her girlhood. It is also the place where “the foundation of her knowledge was really laid,” where she “had uncontrolled use of a library full of books” (24). Yet, while her Grandmother’s house in Albany is a sanctuary of learning for Isabel, it is also a barrier to the outside world. Because she is so absorbed in her library, Isabel “has no wish to look out” on what she considers the “vulgar street” and the “melancholy afternoon” (25).'
var albany_sight = 'Several of Isabel’s characteristics index those of Albany, and of America more generally.  Isabel is repeatedly referred to as “independent”—a trait considered quintessentially American. Like the country, however, she has little real-world experience: she doesn’t “know anything about money” (27), not even how much she has inherited.'
var gardencourt_self = 'Both times Isabel visits Gardencourt—as her first place of residence in the Old World and later when visiting her cousin on his deathbed—it provides an escape from her unsatisfying life. On her first visit, Isabel is full of curiosity and fervor, eager to explore this newfound continent. She is fiercely independent, determined to “know the things one shouldn’t do,” “so as to choose” (70) whether or not to follow society’s standards. The Isabel we encounter on her return to the estate, many years later, is a very different woman: her “soul [is] haunted with terrors” (446), destroyed by a husband who “spoil[s] everything for her that he look[s] at” (447). Upon her return, Isabel sees that “nothing [has] changed; she [recognizes] everything that she had seen years before” (599), which only makes her own transformation all the more striking. '
var gardencourt_sight = 'Gardencourt, the Touchett’s estate in the English countryside, is repeatedly described by Isabel as “picturesque.” The house has both a “name and a history” (4) of which its owner is very proud. Further, it is a place where “privacy reign[s] supreme” (5), making it the perfect sanctuary for Isabel. '
var florence_self = 'Florence marks Isabel’s first venture to the European mainland; her first impression of “what Europe would offer to a young person of taste” (231). Italy, to her, is a “land of promise” (though, as our narrator points out, the country is “imperfectly seen and felt” (231) by our heroine). It is also the place where she first encounters Osmond who, much like Italy itself, has a way of “arrest[ing] her and [holding] her in suspense.” (259). It is ironic, then, that it is in the beautiful villas of Florence that Isabel’s downfall begins. '
var florence_sight = 'Florence is described by James in lush detail, replete with “olive-muffled hills,” “ancient villas,” and a “splendid openness,” all painted “hazy with Italian color” (237). It is a place where “the beautiful might be comforted by endless knowledge” (234); the epitome of Isabel’s European dreams. '
var rome_self = 'The ruins of Rome are the perfect setting for Isabel to reflect on the ruins of her own marriage; on what is left of her European dream. Carrying her “somber spirit from one familiar shrine to the other,” Isabel gazes “through the veil of her personal sadness at the splendid sadness of the scene.” (546) '
var rome_sight = 'In Rome’s “vanished world” (546), the relics of ancient tragedies take on a far less “picturesque” (237) spirit than those of Florence. Instead of fascination and curiosity, they bring to Isabel a “haunting sense of the continuity of the human lot” (546).'

var princeton_self = 'America’s significance in <i> The Sun Also Rises </i> is almost exclusively a notable absence. The expatriates have “lost touch with [American] soil,” (120) but feel no nostalgia for their homeland. They have been ruined by “fake European standards” (120), but have equally little pride in their adopted countries. Any patriotism they once felt toward America has been destroyed by the war. Without any native allegiance, they truly are a “lost generation” (8) lacking a center of gravity.    '
var princeton_sight = 'America, though rarely explicitly described in <i>The Sun Also Rises</i>, has immense importance for our band of expatriates. Our only explicit encounter with America is a description of Robert Cohn’s time at Princeton (though it is not insignificant that this section opens the novel). Cohn is disenchanted with his time at college—he entered school as “a nice boy, a friendly boy” (12) and left with a “painful self-consciousness” of his Jewish heritage and a “flattened nose” (12) from his boxing days.  Cohn’s disillusionment with Princeton is representative of the expatriates’ wider disillusionment with America as a whole—they find the values of their country as meaningless as Cohn’s middleweight boxing championship.'
var paris_self = 'Paris embodies the groups’ collective disillusionment with the Western world. Cohn says he is “sick of Paris” and, although Jake attempts to defend it as a “nice town,” (18) his nighttime tour of restaurants, bars, and clubs in the company of a prostitute says otherwise (22-32). Though there is little love between the expatriates and their adopted city, there is no where else they find more appealing: as Jake says, “going to another country doesn’t make any difference. I’ve tried all that. You can’t get away from yourself by moving from one place to another. There’s nothing to that.” (19)'
var paris_sight = 'The parts of Paris that we are introduced to are indicative of the expatriates’ impressions of the city—bars, dance halls, cafes, and barren apartments give us a sense of extreme loneliness within the bustling city. '
var burguete_self = 'Bill and Jake’s time in Burguete is certainly the happiest in the novel; it is a glimpse, perhaps, of what a simpler life could look like for the expatriates. They walk, fish, picnic, nap on the grassy hillsides, and chat with fellow tourist Harris. The terror of the city and everything it stands for are traded for calmer, undemanding pleasures.'
var burguete_sight = 'Rural Burguete is, in many ways, an antithesis to Paris—the hostess at Jake’s hotel doesn’t even know what a rum punch is (116). The claustrophobic alleyways and avenues of the city are traded for “rolling and grassy” (122) hills and the sound of far-off cowbells, where Bill and Jake fish and picnic in peace. '
var pamplona_self = 'Bullfighting holds something of a grotesque fascination for Jake. He is an “aficionado” (136), who describes with awe and admiration the dance between a bull and a bull-fighter (171). Over the course of the fiesta, however, there is something of a disillusionment for Jake in regards to bullfighting: as Romero becomes just another of Brett’s men and the crowds take on a more and more sinister character, the tone of Jake’s prose turns from appreciation for the fiesta to desperation for an escape.    '
var pamplona_sight = 'The near-magic of the bullfights in Pamplona’s fiesta are juxtaposed with the fiesta’s out-of-control crowds. Their unruly drunkenness turns bullfighting into a spectacle with no respect even for human life: when a spectator is gored at the ring, only a jaded restaurant waiter recognizes that “there is no fun in that” (202).'
var madrid_self = 'Our telling of Jake’s story ends in another bar, in another city, contributing to “the feeling as in a nightmare of it all being something repeated” (71). Jake even admits, when he receives Brett’s telegram summoning him to Madrid, that he “had expected something of the sort” (243). We are left with the sense of Jake’s loss of control as he is pulled, by forces of his past, to a city he views with distaste. '
var madrid_sight = 'Madrid, like Pamplona and Paris, takes on something of a nightmarish quality for Jake. It holds no charm for him; it is only a “high, hot, modern town” (244) with bars and restaurants like any other city.'

var bohemia_self = 'The Shimerdas’ origins affect how others view them and how they view themselves. We are initially introduced to the Shimerdas as a “family from across the water” (10) and Antonia’s Bohemian origin is central to Jim’s impressions of her through the entire narrative. The prevailing attitude on immigrants can perhaps best be summed up in Jim’s friend Jake’s comment on hearing of the Shimerdas: “you were likely to get diseases from foreigners” (10). For the Shimerdas, meanwhile, being Bohemian is a treasured part of their history—so much so that Jim expects that Mr. Shimerda’s spirit will “eventually find its way back to his own country” (81).'
var bohemia_sight = 'Like many immigrants, the Shimerdas simultaneously see America as the Land of Opportunity and idealize their own country in retrospect. For Antonia, Bohemia is a country of blooming flowers and “beautiful talk” (180).'
var virginia_self = 'We only learn about Jim’s past in Virginia through his amazement at the otherness of the West. As Jim is a very young boy, he seems not to feel excitement or nostalgia at leaving his home, instead, we feel a sense of resignation: “If we never arrived anywhere, it did not matter…here, I felt, what would be would be” (13).'
var virginia_sight = 'The only vague descriptions of Jake’s birthplace included in <i> My Antonia </i>are of the “sheep-fold down by the creek” and the “white road that led to mountain pastures” (13). '
var blackhawk_self = 'Jim’s sense of disorientation upon his arrival in this new land is best summed up by his confusion at a downstairs kitchen (14). The community of Black Hawk has much to teach Jim in his formative years, however: he witnesses a diverse set of people held together by their common struggle for survival against the hardships of the frontier. '
var blackhawk_sight = 'Like the rest of the American frontier, Black Hawk is depicted as a place of semi-lawlessness, where subjectivity is “blotted out” (13) by the vastness of nature. In the spirit of Manifest Destiny, the Nebraska frontier is “not a country at all, but the material out of which countries are made” (12). '
var lincoln_self = 'The most distinctive stylistic change accompanying the shift from Black Hawk to Lincoln is the change from predominantly outdoor settings to predominantly indoor ones. Gone are Cather’s expansive descriptions of the countryside, replaced by Jim’s study, where he keeps his books on “shelves [he] had made and painted [himself]” (196).'
var lincoln_sight = 'The shift in <i> My Antonia’s </i> setting from country to city marks a shift in Jim himself. Jim writes that his time of “mental awakening” in Lincoln is “one of the happiest of [his] life” (195). He becomes so absorbed in his studies that he “everything else fade[d] for a time” (195)—indeed, most of his prose in this section focuses on his esteemed professor. Jim’s move to Lincoln also marks a shift in his relationship with Antonia: while he begins his journey on the path to law school, she does not have access to education at all. '
var newyork_self = 'The skyscrapers of New York are symbolic of Jim’s mature life: he has become a high-powered “legal counsel for one of the great Western railways” (3) with a “sympathetic, solicitous interest in women” (5). Jim’s situation is particularly significant in how different it is from Antonia’s adult life on the frontier: before his final visit to her, all Jim hears of Antonia is that she is “poor and [has] a large family” (245). '
var newyork_sight = 'New York is never directly described in<i> My Antonia </i>, but it stands in for the antithesis of the vast, open spaces of Black Hawk.'

//Creates content string for infowindow based on place name (string) and quotes (array of strings)
function content(index, place_name, quotes, images, author) {
   var quotes_string = "<b>" + place_name + "</b> \n <ul>";
    for (i=0; i<quotes.length; i++) {
        quotes_string = quotes_string + "<li> <i>" + quotes[i] + " </i> </li>";
    }
    quotes_string = quotes_string + "</ul>"
    images_string = ""
    for (j = 0; j<images.length; j++) {
        images_string = images_string + images[j];
    }
    var button_string = "";
    if (author == "james") {
        button_string ='<button onclick="update_info_james(' + index +')">Next</button>'
    }
    else if (author == "hemingway") {
        button_string ='<button onclick="update_info_hemingway(' + index + ')">Next</button>'
    }
    else {
        button_string ='<button onclick="update_info_cather(' + index + ')">Next</button>'
    }
    return quotes_string + images_string + "<br /> <br /> <p align=right>" + button_string + '</p>';
}

function content2(self, sight) {
    var content_string = "<p><b>Sight:</b> " + sight + "</p><p>" + "<b>Self:</b> " + self;
    var table_string = "<table><tr><td><b>Sight</b></td><td><b>Self</b></td></tr>";
    table_string  = table_string + "<tr><td>" + sight + "</td><td>" + self + "</td></tr></table>";
    return table_string;
}
function update_info_james(index) {
    var self = "";
    var sight = "";
    if (index == 0) {
        self = albany_self;
        sight = albany_sight;
    }
    else if (index == 1) {
        self = gardencourt_self;
        sight = gardencourt_sight;
    }
    else if (index == 2) {
        self = florence_self;
        sight = florence_sight;
    }
    else {
        self = rome_self;
        sight = rome_sight;
    }
    james_infos[index].setContent(content2(self, sight))
}

function update_info_hemingway(index) {
    var self = "";
    var sight = "";
    if (index == 0) {
        self = princeton_self;
        sight = princeton_sight;
    }
    else if (index == 1) {
        self = paris_self;
        sight = paris_sight;
    }
    else if (index == 2) {
        self = burguete_self;
        sight = burguete_sight;
    }
    else if (index == 3) {
        self = pamplona_self;
        sight = pamplona_sight;
    }
    else {
        self = madrid_self;
        sight = madrid_sight;
    }
    hemingway_infos[index].setContent(content2(self, sight))
}

function update_info_cather(index) {
    var self = "";
    var sight = "";
    if (index == 0) {
        self = bohemia_self;
        sight = bohemia_sight;
    }
    else if (index == 1) {
        self = virginia_self;
        sight = virginia_sight;
    }
    else if (index == 2) {
        self = blackhawk_self;
        sight = blackhawk_sight;
    }
    else if (index == 3) {
        self = lincoln_self;
        sight = lincoln_sight;
    }
    else {
        self = newyork_self;
        sight = newyork_sight;
    }
    cather_infos[index].setContent(content2(self, sight))
}


//Hold information for marker and path objects
var james = [
    {lat: albany.lat, lng: albany.lng, descrip: content(0, "Albany, NY", albany_quotes, albany_images, "james")},
    {lat: gardencourt.lat, lng: gardencourt.lng, descrip: content(1, "Gardencourt, UK", gardencourt_quotes, gardencourt_images, "james")},
    {lat: florence.lat, lng: florence.lng, descrip: content(2, "Florence, Italy", florence_quotes, florence_images, "james")},
    {lat: rome.lat, lng: rome.lng, descrip: content(3, "Rome, Italy", rome_quotes, rome_images, "james")}
];
var james_travel = [
    [albany, gardencourt],
    [gardencourt, florence],
    [florence, rome],
    [rome, gardencourt]
]
var hemingway = [
    {lat: princeton.lat, lng: princeton.lng, descrip: content(0, "Princeton, NJ", princeton_quotes, princeton_images, "hemingway")},
    {lat: paris.lat, lng: paris.lng, descrip: content(1, "Paris, France", paris_quotes, paris_images, "hemingway")},
    {lat: burguete.lat, lng: burguete.lng, descrip: content(2, "Burguete, Spain", burguete_quotes, burguete_images, "hemingway")},
    {lat: pamplona.lat, lng: pamplona.lng, descrip: content(3, "Pamplona, Spain", pamplona_quotes, pamplona_images, "hemingway")},
    {lat: madrid.lat, lng: madrid.lng, descrip: content(4, "Madrid, Spain", madrid_quotes, madrid_images, "hemingway")}
];
var hemingway_travel = [
    [princeton, paris],
    [paris, burguete],
    [burguete, pamplona],
    [pamplona, madrid],
]
var cather = [
    {lat: bohemia.lat, lng: bohemia.lng, descrip: content(0, "Bohemia", bohemia_quotes, bohemia_images, "cather")},
    {lat: virginia.lat, lng: virginia.lng, descrip: content(1, "Virginia", virginia_quotes, virginia_images, "cather")},
    {lat: black_hawk.lat, lng: black_hawk.lng, descrip: content(2, "Black Hawk, NE", blackhawk_quotes, blackhawk_images, "cather")},
    {lat: lincoln.lat, lng: lincoln.lng, descrip: content(3, "Lincoln, NE", lincoln_quotes, lincoln_images, "cather")},
    {lat: new_york.lat, lng: new_york.lng, descrip: content(4, "New York, NY", newyork_quotes, newyork_images, "cather")},
   
];
    var cather_travel = [
    [bohemia, virginia],
    [virginia, black_hawk],
    [black_hawk, lincoln],
    [lincoln, new_york]
]

//Configures map intially
$(function() {

    // styles for map
    // https://developers.google.com/maps/documentation/javascript/styling
    var styles = [

        // hide Google's labels
        {
            featureType: "all",
            elementType: "labels",
            stylers: [
                {visibility: "off"}
            ]
        },

        // hide roads
        {
            featureType: "road",
            elementType: "geometry",
            stylers: [
                {visibility: "off"}
            ]
        }

    ];

    // options for map
    // https://developers.google.com/maps/documentation/javascript/reference#MapOptions
    var options = {
        center: {lat: 37.4236, lng: -50}, // USA
        disableDefaultUI: true,
        mapTypeId: google.maps.MapTypeId.ROADMAP,
        maxZoom: 14,
        panControl: true,
        styles: styles,
        zoom: 3,
        zoomControl: true
    };

    // get DOM node in which map will be instantiated
    var canvas = $("#map-canvas").get(0);

    // instantiate map
    map = new google.maps.Map(canvas, options);

    // configure UI once Google Map is idle (i.e., loaded)
    google.maps.event.addListenerOnce(map, "idle", configure);

});

//Adds marker for place to map given location, description, icon, and novel
function addMarker(la, ln, description, image, novel)
{
    var myLatLng = {lat: la, lng: ln};
    var marker = new google.maps.Marker({
        position: myLatLng,
        map: map,
        icon: image
    });
    marker.setMap(map);
    var infowindow = new google.maps.InfoWindow({
        content: description
    });
    
    marker.addListener('click', function() {
        infowindow.open(map, marker);
    });
    if (novel == "The Sun Also Rises") {
        hemingway_marks.push(marker);
        hemingway_infos.push(infowindow);
    }
    else if (novel == "Portrait of a Lady") {
        james_marks.push(marker);
        james_infos.push(infowindow);
    }
    else if (novel = "My Antonia") {
        cather_marks.push(marker);
        cather_infos.push(infowindow);
    }
}


//Configure and search together run the updating of the map
function configure()
{
    // update UI after map has been dragged
    google.maps.event.addListener(map, "dragend", function() {

        // if info window isn't open
        // http://stackoverflow.com/a/12410385
        if (!info.getMap || !info.getMap())
        {
            update();
        }
    });
    
    map.addListener('click', function(e) {
        update();
    });

    // update UI after zoom level changes
    google.maps.event.addListener(map, "zoom_changed", function() {
        update();
    });

    // configure typeahead
    $("#q").typeahead({
        highlight: false,
        minLength: 1
    },
    {
        display: function(suggestion) { return null; },
        limit: 10,
        source: search,
        templates: {
            suggestion: Handlebars.compile(
                "<div>" +
                "TODO" +
                "</div>"
            )
        }
    });

    // re-center map after place is selected from drop-down
    $("#q").on("typeahead:selected", function(eventObject, suggestion, name) {

        // set map's center
        map.setCenter({lat: parseFloat(suggestion.latitude), lng: parseFloat(suggestion.longitude)});

        // update UI
        update();
    });

    // hide info window when text box has focus
    $("#q").focus(function(eventData) {
        info.close();
    });

    // re-enable ctrl- and right-clicking (and thus Inspect Element) on Google Map
    // https://chrome.google.com/webstore/detail/allow-right-click/hompjdfbfmmmgflfjdlnkohcplmboaeo?hl=en
    document.addEventListener("contextmenu", function(event) {
        event.returnValue = true; 
        event.stopPropagation && event.stopPropagation(); 
        event.cancelBubble && event.cancelBubble();
    }, true);

    // update UI
    update();

    // give focus to text box
    $("#q").focus();
}
function search(query, syncResults, asyncResults)
{
    // get places matching query (asynchronously)
    var parameters = {
        q: query
    };
    $.getJSON(Flask.url_for("search"), parameters)
    .done(function(data, textStatus, jqXHR) {
     
        // call typeahead's callback with search results (i.e., places)
        asyncResults(data);
    })
    .fail(function(jqXHR, textStatus, errorThrown) {

        // log error to browser's console
        console.log(errorThrown.toString());

        // call typeahead's callback with no results
        asyncResults([]);
    });
}

//Shows info window at marker
function showInfo(marker, content)
{
    // start div
    var div = "<div id='info'>";
    if (typeof(content) == "undefined")
    {
        // http://www.ajaxload.info/
        div += "<img alt='loading' src='/static/ajax-loader.gif'/>";
    }
    else
    {
        div += content;
    }

    // end div
    div += "</div>";

    // set info window's content
    info.setContent(div);

    // open info window (if not already open)
    info.open(map, marker);
}

//Adds the markers and paths for James to the map
function addJames()
{
    for (i=0; i<james.length; i++)
        {
            var image = "http://maps.google.com/mapfiles/ms/icons/blue-dot.png";
            addMarker(james[i].lat, james[i].lng, james[i].descrip, image, "Portrait of a Lady");
        }
    for (i=0; i<james_travel.length; i++) {
        var endpoints = james_travel[i];
        var path = new google.maps.Polyline({
            path: endpoints,
            geodesic: true,
            strokeColor: '#4981CE',
            strokeOpacity: 1.0,
            strokeWeight: 2,
            icons: [{
                icon: {path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW},
                offset: '100%'
            }]
        });
        path.setMap(map);
        james_paths.push(path);
    }
}

//Adds the markers and paths for Hemingway to the map
function addHemingway() 
{
     for (i=0; i<hemingway.length; i++)
        {
            var image = "http://maps.google.com/mapfiles/ms/icons/red-dot.png";
            addMarker(hemingway[i].lat, hemingway[i].lng, hemingway[i].descrip, image, "The Sun Also Rises");
        }
    for (i=0; i<hemingway_travel.length; i++) {
        var endpoints = hemingway_travel[i];
        var path = new google.maps.Polyline({
            path: endpoints,
            geodesic: true,
            strokeColor: '#CD5555',
            strokeOpacity: 1.0,
            strokeWeight: 2,
            icons: [{
                icon: {path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW},
                offset: '100%'
            }]
        });
        path.setMap(map);
        hemingway_paths.push(path);
    }
}

//Adds the markers and paths for Cather to the map
function addCather()
{
    for (i=0; i<cather.length; i++)
        {
            var image = "http://maps.google.com/mapfiles/ms/icons/green-dot.png";
            addMarker(cather[i].lat, cather[i].lng, cather[i].descrip, image, "My Antonia");
        }
    for (i=0; i<cather_travel.length; i++) {
        var endpoints = cather_travel[i];
        var path = new google.maps.Polyline({
            path: endpoints,
            geodesic: true,
            strokeColor: '#66CD00',
            strokeOpacity: 1.0,
            strokeWeight: 2,
            icons: [{
                icon: {path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW},
                offset: '100%'
            }]
        });
        path.setMap(map);
        cather_paths.push(path);
    }
}

//Removes the markers and paths for James from the map
function removeJames() {
    for (i=0; i<james_marks.length; i++) {
        james_marks[i].setMap(null);
    }
    
    for (j=0; j<james_paths.length; j++) {
        james_paths[j].setMap(null);
    } 
    
    james_infos = [];
}

//Removes the markers and paths for Hemingway from the map
function removeHemingway() {
    for (i=0; i<hemingway_marks.length; i++) {
        hemingway_marks[i].setMap(null);
    }
    
    for (j=0; j<hemingway_paths.length; j++) {
        hemingway_paths[j].setMap(null);
    } 
    
    hemingway_infos = [];
}

//Removes the markers and paths for Cather from the map
function removeCather() {
    for (i=0; i<cather_marks.length; i++) {
        cather_marks[i].setMap(null);
    }
    
    for (j=0; j<cather_paths.length; j++) {
        cather_paths[j].setMap(null);
    } 
    
    cather_infos = [];
}

//Updates each time something from the drop-down menu is selected
function update() 
{
    var chosen = "View All"
    $(document).on('click', '.dropdown-menu li a', function () {
        chosen = $(this).text();
        if (chosen == "Portrait of a Lady") {
            removeJames();
            removeHemingway();
            removeCather();
            addJames();
        }
        else if (chosen == "The Sun Also Rises") {
            removeJames();
            removeHemingway();
            removeCather();
            addHemingway();
        }
        else if (chosen == "My Antonia") {
            removeJames();
            removeHemingway();
            removeCather();
            addCather();
        }
        else {
            removeJames();
            removeHemingway();
            removeCather();
            addJames();
            addCather();
            addHemingway();
        }
    });
    
};
