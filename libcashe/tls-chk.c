#include <ustr.h>
#include <stdio.h>
#include <gnutls/gnutls.h>
#include <gnutls/crypto.h>
#include <assert.h>

typedef struct Checksum
{
 Ustr *name;
 gnutls_hash_hd_t *ctx;
 
 void  (*update)(struct Checksum *, void *, size_t);
 Ustr *(*digest)(struct Checksum *);
 void  (*free)(struct Checksum *);
} Checksum;

static char hex[] = "0123456789abcdef";
static void asscify(char *out, unsigned char *buf, size_t len)
{
  size_t num = 0;
  
  while (num < len)
  {
    out[num*2 + 0] = hex[buf[num] >> 4];
    out[num*2 + 1] = hex[buf[num] & 0xF];
    ++num;
  }
}

static void chksum__gnutls_update(Checksum *chk, void *buf, size_t len)
{
  gnutls_hash(*chk->ctx, buf, len);
}

#define SHA512_DIGEST_LENGTH 64
static Ustr *chksum__sha512_digest(Checksum *chk)
{
  unsigned char output[SHA512_DIGEST_LENGTH];
  char cstr[SHA512_DIGEST_LENGTH * 2];

  assert(SHA512_DIGEST_LENGTH == gnutls_hash_get_len(GNUTLS_DIG_SHA512));

  gnutls_hash_output(*chk->ctx, output);

  asscify(cstr, output, sizeof(output));
  
  return ustr_dup_buf(cstr, sizeof(cstr));
}

static void chksum__gnutls_free(Checksum *chk, unsigned char *output)
{
  gnutls_hash_deinit(*chk->ctx, output);
  free(chk->ctx);
  ustr_free(chk->name);
  free(chk);
}

static void chksum__sha512_free(Checksum *chk)
{
  unsigned char output[SHA512_DIGEST_LENGTH];

  assert(SHA512_DIGEST_LENGTH == gnutls_hash_get_len(GNUTLS_DIG_SHA512));

  chksum__gnutls_free(chk, output);
}

#define SHA256_DIGEST_LENGTH 32
static Ustr *chksum__sha256_digest(Checksum *chk)
{
  unsigned char output[SHA256_DIGEST_LENGTH];
  char cstr[SHA256_DIGEST_LENGTH * 2];

  assert(SHA256_DIGEST_LENGTH == gnutls_hash_get_len(GNUTLS_DIG_SHA256));

  gnutls_hash_output(*chk->ctx, output);

  asscify(cstr, output, sizeof(output));
  
  return ustr_dup_buf(cstr, sizeof(cstr));
}

static void chksum__sha256_free(Checksum *chk)
{
  unsigned char output[SHA256_DIGEST_LENGTH];

  assert(SHA256_DIGEST_LENGTH == gnutls_hash_get_len(GNUTLS_DIG_SHA256));

  chksum__gnutls_free(chk, output);
}

#define SHA1_DIGEST_LENGTH 20
static Ustr *chksum__sha1_digest(Checksum *chk)
{
  unsigned char output[SHA1_DIGEST_LENGTH];
  char cstr[SHA1_DIGEST_LENGTH * 2];

  assert(SHA1_DIGEST_LENGTH == gnutls_hash_get_len(GNUTLS_DIG_SHA1));

  gnutls_hash_output(*chk->ctx, output);

  asscify(cstr, output, sizeof(output));
  return ustr_dup_buf(cstr, sizeof(cstr));
}

static void chksum__sha1_free(Checksum *chk)
{
  unsigned char output[SHA1_DIGEST_LENGTH];

  assert(SHA1_DIGEST_LENGTH == gnutls_hash_get_len(GNUTLS_DIG_SHA1));
  chksum__gnutls_free(chk, output);
}

#define MD5_DIGEST_LENGTH 16
static Ustr *chksum__md5_digest(Checksum *chk)
{
  unsigned char output[MD5_DIGEST_LENGTH];
  char cstr[MD5_DIGEST_LENGTH * 2];

  assert(MD5_DIGEST_LENGTH == gnutls_hash_get_len(GNUTLS_DIG_MD5));

  gnutls_hash_output(*chk->ctx, output);

  asscify(cstr, output, sizeof(output));
  return ustr_dup_buf(cstr, sizeof(cstr));
}

static void chksum__md5_free(Checksum *chk)
{
  unsigned char output[MD5_DIGEST_LENGTH];

  assert(MD5_DIGEST_LENGTH == gnutls_hash_get_len(GNUTLS_DIG_MD5));
  chksum__gnutls_free(chk, output);
}

static void memerr(Ustr *name)
{
  fprintf(stderr, "malloc(%s): No memory.\n", ustr_cstr(name));
  exit (6);
}

#define EQ_CSTR(x, y) (strcmp(x, y) == 0)
struct Checksum *
checksum_make(const char *name)
{
  Checksum *ret = malloc(sizeof(*ret));

  if (!ret)
    memerr(USTR1(\x8, "checksum"));
  
  if (0) { }
  else if (EQ_CSTR(name, "sha512"))
  {
    gnutls_hash_hd_t *ctx = malloc(sizeof(*ctx));

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    if (gnutls_hash_init(ctx,
                         GNUTLS_DIG_SHA512) < 0)
      memerr(USTR1(\x9, "hash init"));

    ret->name   = USTR1(\6, "sha512");
    ret->ctx    = ctx;
    ret->update = chksum__gnutls_update;
    ret->digest = chksum__sha512_digest;
    ret->free   = chksum__sha512_free;
  }
  else if (EQ_CSTR(name, "sha256"))
  {
    gnutls_hash_hd_t *ctx = malloc(sizeof(*ctx));

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    if (gnutls_hash_init(ctx,
                         GNUTLS_DIG_SHA256) < 0)
      memerr(USTR1(\x9, "hash init"));

    ret->name   = USTR1(\6, "sha256");
    ret->ctx    = ctx;
    ret->update = chksum__gnutls_update;
    ret->digest = chksum__sha256_digest;
    ret->free   = chksum__sha256_free;
  }
  else if (EQ_CSTR(name, "sha1"))
  {
    gnutls_hash_hd_t *ctx = malloc(sizeof(*ctx));

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    if (gnutls_hash_init(ctx,
                         GNUTLS_DIG_SHA1) < 0)
      memerr(USTR1(\x9, "hash init"));

    ret->name   = USTR1(\4, "sha1");
    ret->ctx    = ctx;
    ret->update = chksum__gnutls_update;
    ret->digest = chksum__sha1_digest;
    ret->free   = chksum__sha1_free;
  }
  else if (EQ_CSTR(name, "md5"))
  {
    gnutls_hash_hd_t *ctx = malloc(sizeof(*ctx));

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    if (gnutls_hash_init(ctx,
                         GNUTLS_DIG_MD5) < 0)
      memerr(USTR1(\x9, "hash init"));

    ret->name   = USTR1(\3, "md5");
    ret->ctx    = ctx;
    ret->update = chksum__gnutls_update;
    ret->digest = chksum__md5_digest;
    ret->free   = chksum__md5_free;
  }
  else
  {
    free(ret);
    return NULL;
  }
  
  return ret;
}


int main(int argc, char *argv[])
{
  Checksum *chk = NULL;
  FILE *fp = NULL;
  Ustr *digest = USTR("");

  if (argc < 3)
  {
    fprintf(stderr, "Format: $0 <checksum> <filename>\n");
    exit (1);
  }

  if (!(chk = checksum_make(argv[1])))
  {
    fprintf(stderr, "checksum(%s): Invalid.\n", argv[1]);
    exit (1);
  }
  
  if (!(fp = fopen(argv[2], "r")))
  {
    fprintf(stderr, "open(%s): %m\n", argv[2]);
    exit (1);
  }

  while (!feof(fp))
  {
    char buf[1024];
    size_t len = fread(buf, 1, sizeof(buf), fp);

    chk->update(chk, buf, len);
  }

  fclose(fp);

  digest = chk->digest(chk);

  //  fprintf(stderr, "JDBG:   s=%s\n",  ustr_cstr(chk->name));
  //  fprintf(stderr, "JDBG: len=%zu\n", ustr_len(digest));
  fprintf(stdout, "%s\n", ustr_cstr(digest));

  return 0;
}
