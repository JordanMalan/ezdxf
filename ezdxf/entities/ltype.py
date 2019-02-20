# Created: 17.02.2019
# Copyright (c) 2019, Manfred Moitzi
# License: MIT License
from typing import TYPE_CHECKING, Union, Iterable, cast
from ezdxf.lldxf.attributes import DXFAttr, DXFAttributes, DefSubclass
from ezdxf.lldxf.const import DXF12, SUBCLASS_MARKER
from ezdxf.lldxf.types import DXFTag
from ezdxf.lldxf.tags import Tags
from ezdxf.entities.dxfentity import base_class, SubclassProcessor, DXFEntity
from ezdxf.entities.layer import acdb_symbol_table_record
from ezdxf.tools.complex_ltype import lin_compiler
from .factory import register_entity

if TYPE_CHECKING:
    from ezdxf.eztypes import TagWriter
    from ezdxf.entities.dxfentity import DXFNamespace
    from ezdxf.drawing2 import Drawing

__all__ = ['Linetype']

acdb_linetype = DefSubclass('AcDbLinetypeTableRecord', {
    'name': DXFAttr(2),
    'description': DXFAttr(3, default=''),
    'flags': DXFAttr(70, default=0),
    # 'length': DXFAttr(40),
    # 'items': DXFAttr(73),
})


class LinetypePattern:
    def __init__(self, tags: Tags):
        """ For now just store tags """
        self.tags = tags

    def __len__(self):
        return len(self.tags)

    def export_dxf(self, tagwriter: 'TagWriter'):
        tagwriter.write_tags(self.tags)

    def is_complex_type(self):
        return False


@register_entity
class Linetype(DXFEntity):
    """ DXF LTYPE entity """
    DXFTYPE = 'LTYPE'
    DXFATTRIBS = DXFAttributes(base_class, acdb_symbol_table_record, acdb_linetype)

    def __init__(self, doc: 'Drawing' = None):
        """ Default constructor """
        super().__init__(doc)
        self._pattern_tags = LinetypePattern(Tags())

    @classmethod
    def new(cls, handle: str = None, owner: str = None, dxfattribs: dict = None, doc: 'Drawing' = None) -> 'DXFEntity':
        """
        Constructor for building new entities from scratch by ezdxf (trusted environment)

        Args:
            handle: unique DXF entity handle or None
            owner: owner handle iof entity has an owner else None or '0'
            dxfattribs: DXF attributes to initialize
            doc: DXF document

        """
        dxfattribs = dxfattribs or {}
        pattern = dxfattribs.pop('pattern', [0.0])
        length = dxfattribs.pop('length', 0)  # required for complex types
        ltype = super().new(handle, owner, dxfattribs, doc)  # type: Linetype
        ltype._setup_pattern(pattern, length)
        return ltype

    def load_dxf_attribs(self, processor: SubclassProcessor = None) -> 'DXFNamespace':
        dxf = super().load_dxf_attribs(processor)
        if processor is None:
            return dxf

        tags = processor.load_dxfattribs_into_namespace(dxf, acdb_linetype)
        # store whole subclass
        self._pattern_tags = LinetypePattern(tags)
        return dxf

    def preprocess_export(self, tagwriter: 'TagWriter'):
        if len(self._pattern_tags) == 0:
            return False
        # do not export complex linetypes for DXF12
        if tagwriter.dxfversion == DXF12:
            return not self._pattern_tags.is_complex_type()
        return True

    def export_entity(self, tagwriter: 'TagWriter') -> None:
        super().export_entity(tagwriter)
        # AcDbEntity export is done by parent class
        if tagwriter.dxfversion > DXF12:
            tagwriter.write_tag2(SUBCLASS_MARKER, acdb_symbol_table_record.name)
            tagwriter.write_tag2(SUBCLASS_MARKER, acdb_linetype.name)
        self.dxf.export_dxf_attribs(tagwriter, ['name', 'description', 'flags'], force=True)
        if self._pattern_tags:
            self._pattern_tags.export_dxf(tagwriter)

    def _setup_pattern(self, pattern: Union[Iterable[float], str], length: float) -> None:
        complex_line_type = True if isinstance(pattern, str) else False
        if complex_line_type:  # a .lin like line type definition string
            tags = self._setup_complex_pattern(pattern, length)
        else:
            # pattern: [2.0, 1.25, -0.25, 0.25, -0.25] - 1. element is total pattern length
            # pattern elements: >0 line, <0 gap, =0 point
            tags = Tags([
                DXFTag(72, 65),  # letter 'A'
                DXFTag(73, len(pattern) - 1),
                DXFTag(40, float(pattern[0])),
            ])
            for element in pattern[1:]:
                tags.append(DXFTag(49, float(element)))
                tags.append(DXFTag(74, 0))
        self._pattern_tags = LinetypePattern(tags)

    def _setup_complex_pattern(self, pattern: str, length: float) -> Tags:
        tokens = lin_compiler(pattern)
        tags = Tags([
            DXFTag(72, 65),  # letter 'A'
        ])

        tags2 = [DXFTag(73, 0), DXFTag(40, length)]  # temp length of 0
        count = 0
        for token in tokens:
            if isinstance(token, DXFTag):
                if tags2[-1].code == 49:  # useless 74 only after 49 :))
                    tags2.append(DXFTag(74, 0))
                tags2.append(token)
                count += 1
            else:  # TEXT or SHAPE
                tags2.extend(cast('ComplexLineTypePart', token).complex_ltype_tags(self.doc))
        tags2.append(DXFTag(74, 0))  # useless 74 at the end :))
        tags2[0] = DXFTag(73, count)
        tags.extend(tags2)
        return tags