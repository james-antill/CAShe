#include <ustr.h>
#include <stdio.h>
#include <openssl/md5.h>
#include <openssl/sha.h>

typedef struct Checksum
{
 Ustr *name;
 void *ctx;
 
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

static void chksum__sha512_update(Checksum *chk, void *buf, size_t len)
{
  SHA512_Update(chk->ctx, buf, len);
}

static Ustr *chksum__sha512_digest(Checksum *chk)
{
  unsigned char output[SHA512_DIGEST_LENGTH];
  char cstr[SHA512_DIGEST_LENGTH * 2];

  SHA512_Final(output, chk->ctx);

  asscify(cstr, output, sizeof(output));
  
  return ustr_dup_buf(cstr, sizeof(cstr));
}

static void chksum__openssl_free(Checksum *chk)
{
  free(chk->ctx);
  ustr_free(chk->name);
  free(chk);
}

static void chksum__sha256_update(Checksum *chk, void *buf, size_t len)
{
  SHA256_Update(chk->ctx, buf, len);
}

static Ustr *chksum__sha256_digest(Checksum *chk)
{
  unsigned char output[SHA256_DIGEST_LENGTH];
  char cstr[SHA256_DIGEST_LENGTH * 2];

  SHA256_Final(output, chk->ctx);

  asscify(cstr, output, sizeof(output));
  
  return ustr_dup_buf(cstr, sizeof(cstr));
}

static void chksum__sha1_update(Checksum *chk, void *buf, size_t len)
{
  SHA1_Update(chk->ctx, buf, len);
}

static Ustr *chksum__sha1_digest(Checksum *chk)
{
  unsigned char output[SHA_DIGEST_LENGTH];
  char cstr[SHA_DIGEST_LENGTH * 2];

  SHA1_Final(output, chk->ctx);

  asscify(cstr, output, sizeof(output));
  return ustr_dup_buf(cstr, sizeof(cstr));
}

static void chksum__md5_update(Checksum *chk, void *buf, size_t len)
{
  MD5_Update(chk->ctx, buf, len);
}

static Ustr *chksum__md5_digest(Checksum *chk)
{
  unsigned char output[MD5_DIGEST_LENGTH];
  char cstr[MD5_DIGEST_LENGTH * 2];

  MD5_Final(output, chk->ctx);

  asscify(cstr, output, sizeof(output));
  return ustr_dup_buf(cstr, sizeof(cstr));
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
    SHA512_CTX *ctx = malloc(sizeof(*ctx));

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    SHA512_Init(ctx);
    ret->name   = USTR1(\6, "sha512");
    ret->ctx    = ctx;
    ret->update = chksum__sha512_update;
    ret->digest = chksum__sha512_digest;
    ret->free   = chksum__openssl_free;
  }
  else if (EQ_CSTR(name, "sha256"))
  {
    SHA256_CTX *ctx = malloc(sizeof(*ctx));

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    SHA256_Init(ctx);
    ret->name   = USTR1(\6, "sha256");
    ret->ctx    = ctx;
    ret->update = chksum__sha256_update;
    ret->digest = chksum__sha256_digest;
    ret->free   = chksum__openssl_free;
  }
  else if (EQ_CSTR(name, "sha1"))
  {
    SHA_CTX *ctx = malloc(sizeof(*ctx));

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    SHA1_Init(ctx);
    ret->name   = USTR1(\4, "sha1");
    ret->ctx    = ctx;
    ret->update = chksum__sha1_update;
    ret->digest = chksum__sha1_digest;
    ret->free   = chksum__openssl_free;
  }
  else if (EQ_CSTR(name, "md5"))
  {
    MD5_CTX *ctx = malloc(sizeof(*ctx));

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    MD5_Init(ctx);
    ret->name   = USTR1(\3, "md5");
    ret->ctx    = ctx;
    ret->update = chksum__md5_update;
    ret->digest = chksum__md5_digest;
    ret->free   = chksum__openssl_free;
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
