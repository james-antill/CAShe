
def _link_xdev(src, dst)
{}
def _copy_atomic(src, dst)
{}
def _file2hexdigest(checksum_type, filename, datasize=None, utime=None)
{}


struct Cashe_obj
{
 Ustr *checksum_type;
 Ustr *checksum_data;
};

int cashe_obj_cmp(const struct Cashe_obj *ptr1
                  const struct Cashe_obj *ptr2)
{
  int cmp = ustr_cmp(ptr1->checksum_type, ptr1->checksum_type);

  if (cmp)
    return cmp;
  return ustr_cmp(ptr1->checksum_data, ptr1->checksum_data);
}
int cashe_obj_cmp_eq(const struct Cashe_obj *ptr1
                     const struct Cashe_obj *ptr2)
{
  return cashe_obj_cmp(ptr1, ptr2) == 0;
}

struct Cashe__file_obj
{
 struct Cashe_obj obj;
 Ustr *root;
 int link;

 off_t size;

 int done_stat;
 struct stat stbuf;

 Ustr *cached_filename;
};

struct Cashe_obj *cashe_obj_make(Ustr *root,
                                 Ustr *checksum_type, Ustr *checksum_data)
{
  struct Cashe__obj_file *ret = malloc(sizeof(struct Cashe__obj_file));

  ret->root = root;
  ret->obj.checksum_type = checksum_type;
  ret->obj.checksum_data = checksum_data;

  ret->link = TRUE;
  ret->size = 0;
  ret->done_stat = FALSE;
  ret->cached_filename = NULL;
  
  return &ret->obj;
}

void cashe_obj_free(struct Cashe_obj *obj)
{
  if (!obj)
    return;

  ustr_free(obj->root);
  ustr_free(obj->obj.checksum_type);
  ustr_free(obj->obj.checksum_data);

  ustr_free(obj->cached_filename);

  free(obj);
}

Ustr *cashe_obj_get_dirname(const struct cashe_obj *cobj)
{
  const struct cashe_obj *obj = (const struct cashe__file_obj *)cobj;
  Ustr *ret = ustr_dup(obj->root);

  if (!ret)
    goto err;
  
  ustr_add_cstr(&ret, "/");
  ustr_add(&ret, obj->obj.checksum_type);
  ustr_add_cstr(&ret, "/");
  ustr_add_sub(&ret, obj->obj.checksum_type, 1, 4);

  if (ustr_enomem(ret))
    goto err;
  
  return ret;

 err:
  ustr_free(ret);
  errno = ENOMEM;
  return NULL;
}

Ustr *cashe_obj_get_filename(const struct cashe_obj *cobj)
{
  Ustr *ret = cashe_obj_get_dirname(const struct cashe_obj *cobj);

  if (!ret)
    goto err;
  
  ustr_add_cstr(&ret, "/");
  ustr_add(&ret, obj->obj.checksum_data);

  if (ustr_enomem(ret))
    goto err;
  
  return ret;

 err:
  ustr_free(ret);
  errno = ENOMEM;
  return NULL;
}

static int cashe_obj__stat(const struct cashe_obj *cobj)
{
  const struct cashe_obj *obj = (const struct cashe__file_obj *)cobj;

  if (!ret->done_stat)
  {
    const Ustr *filename = cashe_obj_get_filename(cobj);
    
    if (stat(&obj->stbuf, ustr_cstr(filename)) != -1)
      ret->done_stat = TRUE;
    obj->size = obj->stbuf.st_size;
  }

  return ret->done_stat;
}

off_t cashe_obj_get_len(const struct cashe_obj *cobj)
{
  const struct cashe_obj *obj = (const struct cashe__file_obj *)cobj;

  return obj->size;
}

int cashe_obj_save(const struct cashe_obj *cobj,
                   Ustr *filename, int checksum, int link)
{
}

int cashe_obj_load(const struct cashe_obj *cobj,
                   Ustr *filename, int checksum, int link)
{
}

int cashe_obj_unlink(const struct cashe_obj *cobj)
{
  Ustr *dirname  = cashe_obj_get_dirname(cobj);
  Ustr *filename = cashe_obj_get_filename(cobj);
  const struct cashe_obj *obj = (const struct cashe__file_obj *)cobj;

  ret = unlink(ustr_cstr(filename)) != -1;
  rmdir(ustr_cstr(dirname));

  ret->size = 0;
  ret->done_stat = FALSE;

  return ret;
}

struct CAShe
{
 Ustr *path;
 int try_link;
 int checksum_save;
 int checksum_load;
};

