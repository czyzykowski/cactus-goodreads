# Goodreads plugin for [Cactus](https://github.com/koenbok/Cactus)

Plugin downloads books data from Goodreads API and exposes it to the templates.
One potential use is to generate up to date list of read books.

## Install

Simply copy `goodreads.py` file to your Cactus directory into `plugins/`.

## Configuration

Make sure following keys are present in `config.json`:

 * `goodreads-key`: Goodreads API key. You can obtain it [here](https://www.goodreads.com/api/keys).
 * `goodreads-user-id`: Your user's ID on Goodreads. To get it click on your
   profile picture and note the number from the url. The part just after
   `/user/show/` is your user id.
 * `goodreads-refresh-interval`: (optional) How often the plugin should refresh
   the local copy of the books list. It defaults to 86400, which is 24 hours.
   The call is quite expensive and doing it on every build would slow down the
   whole process too much.

## Usage

Once the plugin is in the repository, it will ask Goodreads API for the whole
list of books from your shelves. It will get exposed to the templates as four
lists:

 * `books` is the complete list of every book,
 * `books_read` is the list from `read` shelf,
 * `books_reading` is the list from `currently-reading` shelf,
 * `books_to_read` is the list from `to-read` shelf.

Each books contains following fields:

 * `title` - book's title,
 * `authors` - comma separated list of book's authors,
 * `date` - date when the book was read,
 * `year` - year when the book was read,
 * `month` - month when the book was read,
 * `link` - link to Goodreads page for the given book,
 * `rating` - number (0-5) of the rating given for the book (0 if no rating was
   present),
 * `shelf` - name of the shelf where the book resides.
