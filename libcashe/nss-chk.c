#include <ustr.h>
#include <stdio.h>
#include <nss.h>
#include <pk11func.h>
#include <assert.h>

typedef struct Checksum
{
 Ustr *name;
 PK11Context *ctx;
 
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

static void chksum__nss_update(Checksum *chk, void *buf, size_t len)
{
  PK11_DigestOp(chk->ctx, buf, len);
}

#define SHA512_DIGEST_LENGTH 64
static Ustr *chksum__sha512_digest(Checksum *chk)
{
  unsigned char output[SHA512_DIGEST_LENGTH+1];
  char cstr[SHA512_DIGEST_LENGTH * 2];
  unsigned int len = 0;
  
  PK11_DigestFinal(chk->ctx, output, &len, sizeof(output));
  assert(len == (sizeof(output)-1));
  
  asscify(cstr, output, sizeof(output));
  
  return ustr_dup_buf(cstr, sizeof(cstr));
}

static void chksum__nss_free(Checksum *chk)
{
  PK11_DestroyContext(chk->ctx, PR_TRUE);
  ustr_free(chk->name);
  free(chk);
}

#define SHA256_DIGEST_LENGTH 32
static Ustr *chksum__sha256_digest(Checksum *chk)
{
  unsigned char output[SHA256_DIGEST_LENGTH+1];
  char cstr[SHA256_DIGEST_LENGTH * 2];
  unsigned int len = 0;
  
  PK11_DigestFinal(chk->ctx, output, &len, sizeof(output));
  assert(len == (sizeof(output)-1));

  asscify(cstr, output, sizeof(output));
  
  return ustr_dup_buf(cstr, sizeof(cstr));
}

#define SHA1_DIGEST_LENGTH 20
static Ustr *chksum__sha1_digest(Checksum *chk)
{
  unsigned char output[SHA1_DIGEST_LENGTH+1];
  char cstr[SHA1_DIGEST_LENGTH * 2];
  unsigned int len = 0;
  
  PK11_DigestFinal(chk->ctx, output, &len, sizeof(output));
  assert(len == (sizeof(output)-1));

  asscify(cstr, output, sizeof(output));
  return ustr_dup_buf(cstr, sizeof(cstr));
}

#define MD5_DIGEST_LENGTH 16
static Ustr *chksum__md5_digest(Checksum *chk)
{
  unsigned char output[MD5_DIGEST_LENGTH+1];
  char cstr[MD5_DIGEST_LENGTH * 2];
  unsigned int len = 0;
  
  PK11_DigestFinal(chk->ctx, output, &len, sizeof(output));
  assert(len == (sizeof(output)-1));

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
  SECStatus s;

  if (!ret)
    memerr(USTR1(\x8, "checksum"));
  
  if (0) { }
  else if (EQ_CSTR(name, "sha512"))
  {
    PK11Context *ctx = PK11_CreateDigestContext(SEC_OID_SHA512);

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    s = PK11_DigestBegin(ctx);
    if (s != SECSuccess)
      memerr(USTR1(\x9, "hash init"));

    ret->name   = USTR1(\6, "sha512");
    ret->ctx    = ctx;
    ret->update = chksum__nss_update;
    ret->digest = chksum__sha512_digest;
    ret->free   = chksum__nss_free;
  }
  else if (EQ_CSTR(name, "sha256"))
  {
    PK11Context *ctx = PK11_CreateDigestContext(SEC_OID_SHA256);

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    s = PK11_DigestBegin(ctx);
    if (s != SECSuccess)
      memerr(USTR1(\x9, "hash init"));

    ret->name   = USTR1(\6, "sha256");
    ret->ctx    = ctx;
    ret->update = chksum__nss_update;
    ret->digest = chksum__sha256_digest;
    ret->free   = chksum__nss_free;
  }
  else if (EQ_CSTR(name, "sha1"))
  {
    PK11Context *ctx = PK11_CreateDigestContext(SEC_OID_SHA1);

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    s = PK11_DigestBegin(ctx);
    if (s != SECSuccess)
      memerr(USTR1(\x9, "hash init"));

    ret->name   = USTR1(\4, "sha1");
    ret->ctx    = ctx;
    ret->update = chksum__nss_update;
    ret->digest = chksum__sha1_digest;
    ret->free   = chksum__nss_free;
  }
  else if (EQ_CSTR(name, "md5"))
  {
    PK11Context *ctx = PK11_CreateDigestContext(SEC_OID_MD5);
    SECStatus s;

    if (!ctx)
      memerr(USTR1(\x3, "ctx"));

    s = PK11_DigestBegin(ctx);
    if (s != SECSuccess)
      memerr(USTR1(\x9, "hash init"));

    ret->name   = USTR1(\3, "md5");
    ret->ctx    = ctx;
    ret->update = chksum__nss_update;
    ret->digest = chksum__md5_digest;
    ret->free   = chksum__nss_free;
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
  // PK11SlotInfo *nssslot = 0;

  if (argc < 3)
  {
    fprintf(stderr, "Format: $0 <checksum> <filename>\n");
    exit (1);
  }

  NSS_NoDB_Init(".");
  //   if (!(nssslot = PK11_GetInternalKeySlot()))
  //   {
  //     fprintf(stderr, "NSS PK11_GetInternalKeySlot: Failed.\n", argv[1]);
  //     exit (1);
  //   }
  
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
