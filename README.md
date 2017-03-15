## Stuff to do:

* There seems to be a bug where the padding for individual padded frames is
  screwed up.

```
(venv) /home/hoafaloaf/workspace/seqparse/test_dir>seqls
/home/hoafaloaf/workspace/seqparse/test_dir/level0.1.exr
/home/hoafaloaf/workspace/seqparse/test_dir/level1/level1.1.exr
/home/hoafaloaf/workspace/seqparse/test_dir/level1/level2/level2.1.exr
/home/hoafaloaf/workspace/seqparse/test_dir/level1/level2/level3/level3.1.exr

(venv) /home/hoafaloaf/workspace/seqparse/test_dir>seqls
/home/hoafaloaf/workspace/seqparse/test_dir/level0.0001,0002.exr
/home/hoafaloaf/workspace/seqparse/test_dir/level1/level1.1.exr
/home/hoafaloaf/workspace/seqparse/test_dir/level1/level2/level2.1.exr
/home/hoafaloaf/workspace/seqparse/test_dir/level1/level2/level3/level3.1.exr

(venv) /home/hoafaloaf/workspace/seqparse/test_dir>
```
